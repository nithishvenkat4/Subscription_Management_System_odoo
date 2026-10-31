from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel

class InvoiceLineResponse(BaseModel):
    id: int
    product_id: Optional[int]
    variant_id: Optional[int]
    description: str
    quantity: int
    unit_price: float
    tax_rate: float
    tax_amount: float
    discount_amount: float
    subtotal: float
    total_amount: float

    class Config:
        from_attributes = True

class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    subscription_id: Optional[int]
    customer_id: int
    issue_date: date
    due_date: date
    payment_terms: str
    status: str
    subtotal: float
    tax_amount: float
    discount_amount: float
    total_amount: float
    amount_paid: float
    outstanding_amount: float
    is_overdue: bool
    notes: Optional[str]
    sent_at: Optional[datetime]
    created_at: datetime
    lines: List[InvoiceLineResponse] = []

    class Config:
        from_attributes = True
