from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class QuotationTemplateLineBase(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = 1
    unit_price: Optional[float] = None

class QuotationTemplateLineCreate(QuotationTemplateLineBase):
    pass

class QuotationTemplateLineResponse(QuotationTemplateLineBase):
    id: int
    template_id: int

    class Config:
        from_attributes = True

class QuotationTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    plan_id: int
    validity_days: int = 30
    is_active: bool = True

class QuotationTemplateCreate(QuotationTemplateBase):
    lines: Optional[List[QuotationTemplateLineCreate]] = []

class QuotationTemplateResponse(QuotationTemplateBase):
    id: int
    created_at: datetime
    lines: List[QuotationTemplateLineResponse] = []

    class Config:
        from_attributes = True
