from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel

class PaymentCreate(BaseModel):
    invoice_id: int
    amount: float
    payment_method: str  # 'Credit Card', 'Bank Transfer', 'Stripe', 'Cash', 'Cheque'
    payment_date: Optional[date] = None
    transaction_reference: Optional[str] = None
    note: Optional[str] = None

class PaymentResponse(BaseModel):
    id: int
    payment_number: str
    invoice_id: int
    customer_id: int
    payment_method: str
    amount: float
    payment_date: date
    transaction_reference: Optional[str]
    note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
