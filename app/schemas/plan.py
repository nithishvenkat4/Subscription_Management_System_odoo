from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel

class PlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    recurring_price: float = 0.0
    billing_interval: str = "monthly"  # 'daily', 'weekly', 'monthly', 'yearly'
    min_quantity: int = 1
    available_from: Optional[date] = None
    available_to: Optional[date] = None
    auto_close_on_end: bool = False
    closable_early: bool = True
    pausable: bool = True
    renewable: bool = True
    is_active: bool = True

class PlanCreate(PlanBase):
    pass

class PlanResponse(PlanBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
