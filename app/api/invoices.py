from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.invoice import Invoice
from app.models.user import User
from app.schemas.invoice import InvoiceResponse
from app.services.invoice_service import InvoiceService
from app.services.billing_engine import BillingEngine
from app.api.deps import get_current_user, get_current_staff_or_admin

router = APIRouter(prefix="/invoices", tags=["Invoices & Billing Day"])

@router.get("", response_model=List[InvoiceResponse])
def list_invoices(
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Invoice)

    if current_user.role == "customer":
        query = query.filter(Invoice.customer_id == current_user.id)
    elif customer_id:
        query = query.filter(Invoice.customer_id == customer_id)

    if status:
        query = query.filter(Invoice.status == status)

    return query.order_by(Invoice.id.desc()).all()

@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    if current_user.role == "customer" and inv.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    return inv

@router.post("/{invoice_id}/confirm", response_model=InvoiceResponse)
def confirm_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_staff_or_admin)
):
    """
    Staff/Admin: Confirm draft invoice (Draft -> Confirmed).
    """
    return InvoiceService.confirm_invoice(db, invoice_id, user)

@router.post("/{invoice_id}/cancel", response_model=InvoiceResponse)
def cancel_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_staff_or_admin)
):
    """
    Staff/Admin: Cancel invoice.
    """
    return InvoiceService.cancel_invoice(db, invoice_id, user)

@router.post("/{invoice_id}/send")
def send_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_staff_or_admin)
):
    """
    Staff/Admin: Send invoice via email.
    """
    return InvoiceService.send_invoice(db, invoice_id, user)

@router.get("/{invoice_id}/print", response_class=HTMLResponse)
def print_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Printable enterprise HTML / PDF invoice.
    """
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    if current_user.role == "customer" and inv.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    html = InvoiceService.generate_html_invoice(inv)
    return HTMLResponse(content=html, status_code=200)

@router.post("/trigger-billing-run")
def trigger_billing_run(
    target_date: Optional[date] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_staff_or_admin)
):
    """
    Billing Day Execution Engine:
    Processes all subscriptions due on or before target_date.
    Guarantees:
    - Nothing is billed twice or skipped
    - Idempotency protection
    - Automatic discount & tax calculation
    - Advancement of billing dates
    """
    result = BillingEngine.run_recurring_billing(
        db=db,
        target_date=target_date or date.today(),
        triggered_by=f"staff:{user.email}"
    )
    return result
