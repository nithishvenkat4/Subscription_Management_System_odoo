from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class QuotationTemplate(Base):
    __tablename__ = "quotation_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    validity_days = Column(Integer, default=30, nullable=False)  # Quote validity window in days
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    plan = relationship("RecurringPlan", back_populates="quotation_templates")
    lines = relationship("QuotationTemplateLine", back_populates="template", cascade="all, delete-orphan")

class QuotationTemplateLine(Base):
    __tablename__ = "quotation_template_lines"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("quotation_templates.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Float, nullable=True)  # If null, dynamically defaults to product.sales_price + variant extra

    template = relationship("QuotationTemplate", back_populates="lines")
    product = relationship("Product")
    variant = relationship("ProductVariant")
