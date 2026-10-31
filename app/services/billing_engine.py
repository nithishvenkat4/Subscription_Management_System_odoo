import calendar
from datetime import date, datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.subscription import Subscription, SubscriptionLine
from app.models.invoice import Invoice, InvoiceLine
from app.models.billing_log import BillingRunLog
from app.services.tax_service import TaxService
from app.services.discount_service import DiscountService

def add_months(sourcedate: date, months: int) -> date:
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

def compute_due_date(issue_date: date, payment_terms: str) -> date:
    terms_lower = (payment_terms or "").lower()
    if "15" in terms_lower:
        return issue_date + timedelta(days=15)
    elif "30" in terms_lower:
        return issue_date + timedelta(days=30)
    elif "60" in terms_lower:
        return issue_date + timedelta(days=60)
    return issue_date  # Immediate Payment

class BillingEngine:

    @staticmethod
    def generate_invoice_number(db: Session) -> str:
        current_year = date.today().year
        last_invoice = db.query(Invoice).filter(Invoice.invoice_number.like(f"INV-{current_year}-%")).order_by(Invoice.id.desc()).first()
        if last_invoice and last_invoice.invoice_number:
            try:
                seq = int(last_invoice.invoice_number.split("-")[-1]) + 1
            except ValueError:
                seq = db.query(Invoice).count() + 1
        else:
            seq = 1
        return f"INV-{current_year}-{seq:05d}"

    @staticmethod
    def advance_billing_date(current_billing_date: date, interval: str) -> date:
        intv = (interval or "monthly").lower()
        if intv == "daily":
            return current_billing_date + timedelta(days=1)
        elif intv == "weekly":
            return current_billing_date + timedelta(days=7)
        elif intv == "yearly":
            try:
                return current_billing_date.replace(year=current_billing_date.year + 1)
            except ValueError: # Leap day Feb 29
                return current_billing_date.replace(year=current_billing_date.year + 1, day=28)
        else: # monthly
            return add_months(current_billing_date, 1)

    @classmethod
    def run_recurring_billing(
        cls,
        db: Session,
        target_date: Optional[date] = None,
        triggered_by: str = "automated_cron"
    ) -> Dict[str, Any]:
        """
        Executes automated recurring billing run for all due subscriptions.
        Guarantees:
        - ZERO DOUBLE BILLING: Uses cycle-specific idempotency keys.
        - ZERO SKIPPED CYCLES: Iterates all active subscriptions due on or before target_date.
        - AUTOMATIC TAX & DISCOUNT APPLICATION.
        - ATOMIC ADVANCEMENT of next_billing_date.
        - AUTO-CLOSE ENFORCEMENT for plans configured with auto_close_on_end.
        """
        if not target_date:
            target_date = date.today()

        # Fetch active subscriptions due for billing
        due_subscriptions = db.query(Subscription).filter(
            Subscription.status == "active",
            Subscription.next_billing_date <= target_date
        ).all()

        evaluated_count = len(due_subscriptions)
        created_invoices: List[Invoice] = []
        skipped_count = 0
        error_count = 0
        log_messages = []

        for sub in due_subscriptions:
            try:
                cycle_date = sub.next_billing_date
                idempotency_key = f"SUB-{sub.id}-{cycle_date.isoformat()}"

                # Idempotency Check: prevent duplicate billing
                existing_invoice = db.query(Invoice).filter(
                    Invoice.idempotency_key == idempotency_key
                ).first()
                if existing_invoice:
                    skipped_count += 1
                    log_messages.append(f"Subscription #{sub.subscription_number}: Skipped (already billed under {existing_invoice.invoice_number})")
                    continue

                # Prepare Invoice Lines
                inv_lines = []
                subtotal = 0.0
                tax_total = 0.0
                product_ids = []
                total_qty = 0

                for sline in sub.lines:
                    line_subtotal = round(sline.quantity * sline.unit_price, 2)
                    tax_rate, line_tax = TaxService.calculate_line_tax(sline.tax_rule, line_subtotal)
                    
                    subtotal += line_subtotal
                    tax_total += line_tax
                    total_qty += sline.quantity
                    if sline.product_id:
                        product_ids.append(sline.product_id)

                    inv_lines.append(InvoiceLine(
                        product_id=sline.product_id,
                        variant_id=sline.variant_id,
                        description=sline.description or (sline.product.name if sline.product else "Subscription Line"),
                        quantity=sline.quantity,
                        unit_price=sline.unit_price,
                        tax_rate=tax_rate,
                        tax_amount=line_tax,
                        discount_amount=0.0,
                        subtotal=line_subtotal,
                        total_amount=round(line_subtotal + line_tax, 2)
                    ))

                # Automatic Discount Evaluation
                discount_amount = 0.0
                applied_rule = None
                discount_eval = DiscountService.get_eligible_discount(
                    db=db,
                    subtotal=subtotal,
                    total_quantity=total_qty,
                    target_product_ids=product_ids,
                    discount_id=sub.applied_discount_id
                )
                if discount_eval:
                    applied_rule, discount_amount = discount_eval
                    DiscountService.record_discount_application(db, applied_rule)

                total_amount = max(0.0, round(subtotal + tax_total - discount_amount, 2))
                due_date = compute_due_date(cycle_date, sub.payment_terms)
                inv_num = cls.generate_invoice_number(db)

                invoice = Invoice(
                    invoice_number=inv_num,
                    subscription_id=sub.id,
                    customer_id=sub.customer_id,
                    idempotency_key=idempotency_key,
                    issue_date=cycle_date,
                    due_date=due_date,
                    payment_terms=sub.payment_terms,
                    status="draft", # Created as Draft, team can confirm, send or print
                    subtotal=subtotal,
                    tax_amount=tax_total,
                    discount_amount=discount_amount,
                    total_amount=total_amount,
                    amount_paid=0.0,
                    notes=f"Auto-generated recurring invoice for Subscription {sub.subscription_number} ({sub.plan.name if sub.plan else 'Plan'})."
                )
                invoice.lines = inv_lines
                db.add(invoice)
                db.flush() # Flush to get invoice ID

                # Advance subscription next_billing_date
                interval = sub.plan.billing_interval if sub.plan else "monthly"
                next_date = cls.advance_billing_date(sub.next_billing_date, interval)
                sub.next_billing_date = next_date

                # Check auto-close on end rule
                if sub.auto_close_on_end and sub.expiry_date and next_date > sub.expiry_date:
                    sub.status = "closed"
                    log_messages.append(f"Subscription #{sub.subscription_number}: Cycle billed, subscription auto-closed upon reaching expiry date.")
                else:
                    log_messages.append(f"Subscription #{sub.subscription_number}: Invoiced as {inv_num}, next billing date {next_date.isoformat()}.")

                created_invoices.append(invoice)

            except Exception as e:
                error_count += 1
                log_messages.append(f"Subscription #{sub.subscription_number} Error: {str(e)}")

        db.commit()

        # Record Billing Run Log
        run_log = BillingRunLog(
            run_date=datetime.now(timezone.utc),
            triggered_by=triggered_by,
            subscriptions_evaluated=evaluated_count,
            invoices_created=len(created_invoices),
            subscriptions_skipped=skipped_count,
            errors_count=error_count,
            details="\n".join(log_messages)
        )
        db.add(run_log)
        db.commit()

        return {
            "success": True,
            "evaluated": evaluated_count,
            "created": len(created_invoices),
            "skipped": skipped_count,
            "errors": error_count,
            "invoice_numbers": [inv.invoice_number for inv in created_invoices],
            "log": log_messages
        }
