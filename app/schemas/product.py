from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class ProductVariantBase(BaseModel):
    attribute_name: str
    attribute_value: str
    extra_price: float = 0.0
    sku: Optional[str] = None
    is_active: bool = True

class ProductVariantCreate(ProductVariantBase):
    pass

class ProductVariantResponse(ProductVariantBase):
    id: int
    product_id: int

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    product_type: str = "software"
    sales_price: float = 0.0
    cost_price: float = 0.0
    notes: Optional[str] = None
    is_active: bool = True

class ProductCreate(ProductBase):
    variants: Optional[List[ProductVariantCreate]] = []

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    variants: List[ProductVariantResponse] = []

    class Config:
        from_attributes = True
