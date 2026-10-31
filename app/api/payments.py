from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.payment import Payment
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services.payment_service import PaymentService
from app.api.deps import get_current_user, get_current_staff_or_admin

router = APIRouter(prefix="/payments", tags=["Payments & Reconciliation"])

@router.get("", response_model=List[PaymentResponse])
def list_payments(
    invoice_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Payment)

    if current_user.role == "customer":
        query = query.filter(Payment.customer_id == current_user.id)
    elif customer_id:
        query = query.filter(Payment.customer_id == customer_id)

    if invoice_id:
        query = query.filter(Payment.invoice_id == invoice_id)

    return query.order_by(Payment.payment_date.desc(), Payment.id.desc()).all()

@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def record_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_or_admin)
):
    """
    Staff/Admin: Record payment against an invoice.
    Updates amount paid and auto-marks invoice as 'paid' when fully reconciled.
    """
    payment = PaymentService.record_payment(
        db=db,
        invoice_id=payload.invoice_id,
        amount=payload.amount,
        payment_method=payload.payment_method,
        payment_date=payload.payment_date,
        transaction_reference=payload.transaction_reference,
        note=payload.note,
        current_user=current_user
    )
    return payment

@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found.")

    if current_user.role == "customer" and payment.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    return payment
