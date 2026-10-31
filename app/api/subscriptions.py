from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.subscription import Subscription, SubscriptionLine
from app.models.plan import RecurringPlan
from app.models.product import Product, ProductVariant
from app.models.quote_template import QuotationTemplate
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionStatusUpdate
)
from app.services.tax_service import TaxService
from app.services.discount_service import DiscountService
from app.api.deps import get_current_user, get_current_staff_or_admin

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions & Quotations"])

def generate_subscription_number(db: Session) -> str:
    current_year = date.today().year
    last_sub = db.query(Subscription).filter(Subscription.subscription_number.like(f"SUB-{current_year}-%")).order_by(Subscription.id.desc()).first()
    if last_sub and last_sub.subscription_number:
        try:
            seq = int(last_sub.subscription_number.split("-")[-1]) + 1
        except ValueError:
            seq = db.query(Subscription).count() + 1
    else:
        seq = 1
    return f"SUB-{current_year}-{seq:05d}"

@router.get("", response_model=List[SubscriptionResponse])
def list_subscriptions(
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List subscriptions.
    - Customers strictly see only their own subscriptions.
    - Staff/Admin can see all subscriptions and filter by customer or status.
    """
    query = db.query(Subscription)

    if current_user.role == "customer":
        query = query.filter(Subscription.customer_id == current_user.id)
    elif customer_id:
        query = query.filter(Subscription.customer_id == customer_id)

    if status:
        query = query.filter(Subscription.status == status)

    return query.order_by(Subscription.id.desc()).all()

@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription_or_quote(
    payload: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new Subscription / Sales Quotation.
    Can be created manually or from a Quotation Template.
    """
    plan = db.query(RecurringPlan).filter(RecurringPlan.id == payload.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")

    # Target customer
    cust_id = payload.customer_id
    if current_user.role == "customer":
        cust_id = current_user.id  # enforce self-service

    # Auto-generate number
    sub_num = generate_subscription_number(db)

    # Calculate quote validity if template used
    quote_valid_until = None
    if payload.quotation_template_id:
        tmpl = db.query(QuotationTemplate).filter(QuotationTemplate.id == payload.quotation_template_id).first()
        if tmpl and tmpl.validity_days:
            quote_valid_until = date.today() + timedelta(days=tmpl.validity_days)

    subscription = Subscription(
        subscription_number=sub_num,
        customer_id=cust_id,
        plan_id=plan.id,
        quotation_template_id=payload.quotation_template_id,
        start_date=payload.start_date,
        expiry_date=payload.expiry_date,
        next_billing_date=payload.start_date,
        quote_valid_until=quote_valid_until,
        payment_terms=payload.payment_terms,
        status="draft", # Starts as draft
        auto_close_on_end=plan.auto_close_on_end,
        closable_early=plan.closable_early,
        pausable=plan.pausable,
        renewable=plan.renewable,
        applied_discount_id=payload.applied_discount_id,
        notes=payload.notes
    )
    db.add(subscription)
    db.flush()

    # Process Lines
    subtotal = 0.0
    tax_total = 0.0
    total_qty = 0
    product_ids = []
    lines_to_add = []

    # If payload lines provided, use them; if empty and template provided, populate from template
    raw_lines = payload.lines
    if not raw_lines and payload.quotation_template_id:
        tmpl = db.query(QuotationTemplate).filter(QuotationTemplate.id == payload.quotation_template_id).first()
        if tmpl:
            for tl in tmpl.lines:
                lines_to_add.append({
                    "product_id": tl.product_id,
                    "variant_id": tl.variant_id,
                    "description": tl.product.name if tl.product else "Service Line",
                    "quantity": tl.quantity,
                    "unit_price": tl.unit_price,
                    "tax_id": None
                })
    else:
        for l in raw_lines:
            lines_to_add.append({
                "product_id": l.product_id,
                "variant_id": l.variant_id,
                "description": l.description,
                "quantity": l.quantity,
                "unit_price": l.unit_price,
                "tax_id": l.tax_id
            })

    # Validate minimum quantity required by plan
    total_quantity_ordered = sum(item["quantity"] for item in lines_to_add)
    if total_quantity_ordered < plan.min_quantity:
        raise HTTPException(
            status_code=400,
            detail=f"This plan requires a minimum quantity of {plan.min_quantity} seats/units (ordered: {total_quantity_ordered})."
        )

    for item in lines_to_add:
        prod = db.query(Product).filter(Product.id == item["product_id"]).first()
        unit_price = item["unit_price"]
        if unit_price is None or unit_price == 0.0:
            base_p = prod.sales_price if prod else 0.0
            extra_p = 0.0
            if item["variant_id"]:
                var = db.query(ProductVariant).filter(ProductVariant.id == item["variant_id"]).first()
                extra_p = var.extra_price if var else 0.0
            unit_price = base_p + extra_p

        line_sub = round(item["quantity"] * unit_price, 2)
        tax_rate, line_tax = 0.0, 0.0
        if item.get("tax_id"):
            t_rule = TaxService.get_tax_rule(db, item["tax_id"])
            tax_rate, line_tax = TaxService.calculate_line_tax(t_rule, line_sub)

        subtotal += line_sub
        tax_total += line_tax
        total_qty += item["quantity"]
        product_ids.append(item["product_id"])

        sline = SubscriptionLine(
            subscription_id=subscription.id,
            product_id=item["product_id"],
            variant_id=item.get("variant_id"),
            description=item.get("description") or (prod.name if prod else "Subscription Line"),
            quantity=item["quantity"],
            unit_price=unit_price,
            tax_id=item.get("tax_id"),
            tax_rate=tax_rate,
            tax_amount=line_tax,
            discount_amount=0.0,
            subtotal=line_sub,
            total_amount=round(line_sub + line_tax, 2)
        )
        db.add(sline)

    # Evaluate discount
    discount_amount = 0.0
    discount_eval = DiscountService.get_eligible_discount(
        db=db,
        subtotal=subtotal,
        total_quantity=total_qty,
        target_product_ids=product_ids,
        discount_id=payload.applied_discount_id
    )
    if discount_eval:
        applied_rule, discount_amount = discount_eval

    subscription.subtotal = subtotal
    subscription.tax_total = tax_total
    subscription.discount_total = discount_amount
    subscription.recurring_total = max(0.0, round(subtotal + tax_total - discount_amount, 2))

    db.commit()
    db.refresh(subscription)
    return subscription

@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found.")

    if current_user.role == "customer" and sub.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    return sub

@router.patch("/{subscription_id}/status", response_model=SubscriptionResponse)
def update_subscription_status(
    subscription_id: int,
    payload: SubscriptionStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enforces subscription state machine:
    - Draft -> Quotation -> Confirmed -> Active -> Closed
    - Active -> Paused (only if plan.pausable is True)
    - Active -> Closed (only if plan.closable_early is True)
    """
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found.")

    new_status = payload.status.lower()
    allowed_statuses = ["draft", "quotation", "confirmed", "active", "paused", "closed"]
    if new_status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status '{new_status}'.")

    # Policy checks
    if new_status == "paused" and not sub.pausable:
        raise HTTPException(status_code=400, detail="This subscription plan does not allow pausing.")

    if new_status == "closed" and sub.status == "active" and not sub.closable_early:
        # Check if expired
        if sub.expiry_date and date.today() < sub.expiry_date:
            raise HTTPException(status_code=400, detail="This subscription plan cannot be closed early before its expiry date.")

    sub.status = new_status
    db.commit()
    db.refresh(sub)
    return sub
