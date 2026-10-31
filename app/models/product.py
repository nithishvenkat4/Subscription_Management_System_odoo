from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    product_type = Column(String(50), default="software", nullable=False)  # 'software', 'service', 'addon', 'consumable'
    sales_price = Column(Float, default=0.0, nullable=False)
    cost_price = Column(Float, default=0.0, nullable=False)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")

class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    attribute_name = Column(String(100), nullable=False)  # e.g., 'Brand', 'Storage Tier', 'Hosting'
    attribute_value = Column(String(100), nullable=False) # e.g., 'Odoo', 'Enterprise', 'Cloud'
    extra_price = Column(Float, default=0.0, nullable=False) # e.g. 560.00
    sku = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)

    product = relationship("Product", back_populates="variants")
