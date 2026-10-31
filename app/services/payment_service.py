from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.payment import Payment
from app.models.invoice import Invoice
from app.models.user import User

class PaymentService:

    @staticmethod
    def generate_payment_number(db: Session) -> str:
        current_year = date.today().year
        last_pay = db.query(Payment).filter(Payment.payment_number.like(f"PAY-{current_year}-%")).order_by(Payment.id.desc()).first()
        if last_pay and last_pay.payment_number:
            try:
                seq = int(last_pay.payment_number.split("-")[-1]) + 1
            except ValueError:
                seq = db.query(Payment).count() + 1
        else:
            seq = 1
        return f"PAY-{current_year}-{seq:05d}"

    @classmethod
    def record_payment(
        cls,
        db: Session,
        invoice_id: int,
        amount: float,
        payment_method: str,
        payment_date: Optional[date] = None,
        transaction_reference: Optional[str] = None,
        note: Optional[str] = None,
        current_user: Optional[User] = None
    ) -> Payment:
        """
        Records payment against an invoice and updates its financial balance and status.
        """
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found.")

        if invoice.status == "cancelled":
            raise HTTPException(status_code=400, detail="Cannot record payment against a cancelled invoice.")

        # If invoice is in draft, auto-confirm it upon receiving payment
        if invoice.status == "draft":
            invoice.status = "confirmed"

        if amount <= 0:
            raise HTTPException(status_code=400, detail="Payment amount must be greater than zero.")

        outstanding = invoice.outstanding_amount
        if round(amount, 2) > round(outstanding, 2):
            raise HTTPException(
                status_code=400,
                detail=f"Payment amount (${amount:,.2f}) exceeds outstanding invoice balance (${outstanding:,.2f})."
            )

        pay_num = cls.generate_payment_number(db)
        payment = Payment(
            payment_number=pay_num,
            invoice_id=invoice.id,
            customer_id=invoice.customer_id,
            payment_method=payment_method,
            amount=round(amount, 2),
            payment_date=payment_date or date.today(),
            transaction_reference=transaction_reference,
            note=note,
            created_by_id=current_user.id if current_user else None
        )
        db.add(payment)

        # Update invoice amount paid
        invoice.amount_paid = round(invoice.amount_paid + amount, 2)
        if invoice.amount_paid >= invoice.total_amount:
            invoice.status = "paid"

        db.commit()
        db.refresh(payment)
        return payment
