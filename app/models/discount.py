from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class DiscountRule(Base):
    __tablename__ = "discount_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    discount_type = Column(String(50), nullable=False, default="percentage")  # 'percentage' or 'fixed_amount'
    discount_value = Column(Float, nullable=False, default=0.0)  # e.g., 15.0 (%) or 50.0 ($)
    
    # Eligibility Criteria
    min_purchase_amount = Column(Float, default=0.0, nullable=False)
    min_quantity = Column(Integer, default=0, nullable=False)
    
    # Date Range
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    # Usage Ceiling
    max_uses = Column(Integer, nullable=True)  # None = unlimited
    used_count = Column(Integer, default=0, nullable=False)
    
    # Scope: 'whole_subscription' or 'specific_products'
    scope = Column(String(50), default="whole_subscription", nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    target_product = relationship("Product", foreign_keys=[product_id])
