from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class TaxRuleBase(BaseModel):
    name: str
    rate: float = 0.0
    tax_type: str = "percentage"
    description: Optional[str] = None
    is_active: bool = True

class TaxRuleCreate(TaxRuleBase):
    pass

class TaxRuleResponse(TaxRuleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
