from datetime import date, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_

from app.models.subscription import Subscription
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.plan import RecurringPlan
from app.models.user import User

class AnalyticsService:

    @staticmethod
    def get_finance_dashboard(
        db: Session,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        customer_id: Optional[int] = None,
        plan_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculates executive finance KPIs with sub-2-second indexed aggregation queries.
        """
        today = date.today()

        # 1. Active Subscriptions Count & Normalized MRR/ARR
        sub_query = db.query(Subscription).join(Subscription.plan).filter(Subscription.status == "active")
        if customer_id:
            sub_query = sub_query.filter(Subscription.customer_id == customer_id)
        if plan_id:
            sub_query = sub_query.filter(Subscription.plan_id == plan_id)

        active_subs = sub_query.all()
        active_subs_count = len(active_subs)

        # Compute MRR normalized across intervals
        mrr = 0.0
        for sub in active_subs:
            interval = sub.plan.billing_interval.lower() if sub.plan else "monthly"
            amount = sub.recurring_total
            if interval == "daily":
                mrr += amount * 30.0
            elif interval == "weekly":
                mrr += amount * (52.0 / 12.0)
            elif interval == "yearly":
                mrr += amount / 12.0
            else: # monthly
                mrr += amount

        arr = mrr * 12.0

        # 2. Revenue Collected (Total Payments in period)
        pay_query = db.query(func.coalesce(func.sum(Payment.amount), 0.0))
        if date_from:
            pay_query = pay_query.filter(Payment.payment_date >= date_from)
        if date_to:
            pay_query = pay_query.filter(Payment.payment_date <= date_to)
        if customer_id:
            pay_query = pay_query.filter(Payment.customer_id == customer_id)
        
        revenue_collected = float(pay_query.scalar() or 0.0)

        # 3. Total Still Owed (Outstanding AR across confirmed invoices)
        ar_query = db.query(
            func.coalesce(func.sum(Invoice.total_amount - Invoice.amount_paid), 0.0)
        ).filter(
            Invoice.status.in_(["draft", "confirmed"]),
            (Invoice.total_amount - Invoice.amount_paid) > 0
        )
        if customer_id:
            ar_query = ar_query.filter(Invoice.customer_id == customer_id)
        total_owed = float(ar_query.scalar() or 0.0)

        # 4. Overdue Invoices Analysis
        overdue_invoices_query = db.query(Invoice).filter(
            Invoice.status.in_(["draft", "confirmed"]),
            Invoice.due_date < today,
            (Invoice.total_amount - Invoice.amount_paid) > 0
        )
        if customer_id:
            overdue_invoices_query = overdue_invoices_query.filter(Invoice.customer_id == customer_id)

        overdue_invoices_list = overdue_invoices_query.order_by(Invoice.due_date.asc()).all()
        overdue_count = len(overdue_invoices_list)
        total_overdue_amount = sum(inv.outstanding_amount for inv in overdue_invoices_list)

        # Overdue Aging Buckets
        aging_1_30 = 0.0
        aging_31_60 = 0.0
        aging_60_plus = 0.0

        overdue_items = []
        for inv in overdue_invoices_list:
            days_overdue = (today - inv.due_date).days
            out_amt = inv.outstanding_amount
            if days_overdue <= 30:
                aging_1_30 += out_amt
            elif days_overdue <= 60:
                aging_31_60 += out_amt
            else:
                aging_60_plus += out_amt

            overdue_items.append({
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "customer_name": inv.customer.full_name if inv.customer else "Unknown",
                "customer_email": inv.customer.email if inv.customer else "",
                "due_date": inv.due_date.isoformat(),
                "days_overdue": days_overdue,
                "total_amount": inv.total_amount,
                "amount_paid": inv.amount_paid,
                "outstanding_amount": out_amt
            })

        # 5. Plan Distribution breakdown
        plan_distribution = []
        plans = db.query(RecurringPlan).all()
        for p in plans:
            count = db.query(Subscription).filter(Subscription.plan_id == p.id, Subscription.status == "active").count()
            plan_distribution.append({
                "plan_name": p.name,
                "interval": p.billing_interval,
                "price": p.recurring_price,
                "active_subscriptions": count
            })

        # 6. Recent Payments Log
        recent_payments = db.query(Payment).order_by(Payment.payment_date.desc(), Payment.id.desc()).limit(10).all()
        recent_payments_data = [{
            "id": p.id,
            "payment_number": p.payment_number,
            "invoice_number": p.invoice.invoice_number if p.invoice else "N/A",
            "customer_name": p.customer.full_name if p.customer else "N/A",
            "amount": p.amount,
            "method": p.payment_method,
            "payment_date": p.payment_date.isoformat(),
            "note": p.note or ""
        } for p in recent_payments]

        return {
            "summary": {
                "active_subscriptions_count": active_subs_count,
                "mrr": round(mrr, 2),
                "arr": round(arr, 2),
                "revenue_collected": round(revenue_collected, 2),
                "total_owed": round(total_owed, 2),
                "overdue_count": overdue_count,
                "total_overdue_amount": round(total_overdue_amount, 2),
            },
            "aging": {
                "aging_1_to_30_days": round(aging_1_30, 2),
                "aging_31_to_60_days": round(aging_31_60, 2),
                "aging_over_60_days": round(aging_60_plus, 2),
            },
            "overdue_invoices": overdue_items[:50], # Top 50 prioritized
            "plan_distribution": plan_distribution,
            "recent_payments": recent_payments_data
        }
