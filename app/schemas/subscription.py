from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel

class SubscriptionLineBase(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    description: Optional[str] = None
    quantity: int = 1
    unit_price: float
    tax_id: Optional[int] = None

class SubscriptionLineCreate(SubscriptionLineBase):
    pass

class SubscriptionLineResponse(SubscriptionLineBase):
    id: int
    tax_rate: float
    tax_amount: float
    discount_amount: float
    subtotal: float
    total_amount: float

    class Config:
        from_attributes = True

class SubscriptionBase(BaseModel):
    customer_id: int
    plan_id: int
    quotation_template_id: Optional[int] = None
    start_date: date
    expiry_date: Optional[date] = None
    payment_terms: str = "Immediate Payment"
    notes: Optional[str] = None
    applied_discount_id: Optional[int] = None

class SubscriptionCreate(SubscriptionBase):
    lines: List[SubscriptionLineCreate] = []

class SubscriptionStatusUpdate(BaseModel):
    status: str  # 'quotation', 'confirmed', 'active', 'paused', 'closed'

class SubscriptionResponse(SubscriptionBase):
    id: int
    subscription_number: str
    next_billing_date: date
    quote_valid_until: Optional[date] = None
    status: str
    auto_close_on_end: bool
    closable_early: bool
    pausable: bool
    renewable: bool
    subtotal: float
    tax_total: float
    discount_total: float
    recurring_total: float
    created_at: datetime
    lines: List[SubscriptionLineResponse] = []

    class Config:
        from_attributes = True
