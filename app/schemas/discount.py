from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel

class DiscountRuleBase(BaseModel):
    name: str
    discount_type: str = "percentage"  # 'percentage' or 'fixed_amount'
    discount_value: float = 0.0
    min_purchase_amount: float = 0.0
    min_quantity: int = 0
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    max_uses: Optional[int] = None
    scope: str = "whole_subscription"  # 'whole_subscription' or 'specific_products'
    product_id: Optional[int] = None
    is_active: bool = True

class DiscountRuleCreate(DiscountRuleBase):
    pass

class DiscountRuleResponse(DiscountRuleBase):
    id: int
    used_count: int
    created_at: datetime

    class Config:
        from_attributes = True
