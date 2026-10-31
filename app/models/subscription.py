from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    subscription_number = Column(String(50), unique=True, index=True, nullable=False) # e.g. SUB-2026-0001
    customer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False, index=True)
    quotation_template_id = Column(Integer, ForeignKey("quotation_templates.id", ondelete="SET NULL"), nullable=True)
    
    # Dates
    start_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    next_billing_date = Column(Date, nullable=False, index=True)
    quote_valid_until = Column(Date, nullable=True)
    
    # Terms & Status
    payment_terms = Column(String(100), default="Immediate Payment", nullable=False) # 'Immediate Payment', 'Net 15', 'Net 30'
    status = Column(String(50), default="draft", nullable=False, index=True) # 'draft', 'quotation', 'confirmed', 'active', 'paused', 'closed'
    
    # Inherited or Custom Lifecycle Flags
    auto_close_on_end = Column(Boolean, default=False)
    closable_early = Column(Boolean, default=True)
    pausable = Column(Boolean, default=True)
    renewable = Column(Boolean, default=True)
    
    # Financial Totals (Per Billing Cycle)
    subtotal = Column(Float, default=0.0, nullable=False)
    tax_total = Column(Float, default=0.0, nullable=False)
    discount_total = Column(Float, default=0.0, nullable=False)
    recurring_total = Column(Float, default=0.0, nullable=False)
    
    # Discount rule linkage if applied
    applied_discount_id = Column(Integer, ForeignKey("discount_rules.id", ondelete="SET NULL"), nullable=True)
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    customer = relationship("User", back_populates="subscriptions", foreign_keys=[customer_id])
    plan = relationship("RecurringPlan", back_populates="subscriptions")
    template = relationship("QuotationTemplate")
    applied_discount = relationship("DiscountRule")
    lines = relationship("SubscriptionLine", back_populates="subscription", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="subscription")

    # Composite Index for High Performance SLA (< 2s)
    __table_args__ = (
        Index("idx_sub_status_billing", "status", "next_billing_date"),
        Index("idx_sub_cust_status", "customer_id", "status"),
    )

class SubscriptionLine(Base):
    __tablename__ = "subscription_lines"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)
    description = Column(String(255), nullable=True)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Float, default=0.0, nullable=False)
    tax_id = Column(Integer, ForeignKey("tax_rules.id", ondelete="SET NULL"), nullable=True)
    tax_rate = Column(Float, default=0.0, nullable=False)
    tax_amount = Column(Float, default=0.0, nullable=False)
    discount_amount = Column(Float, default=0.0, nullable=False)
    subtotal = Column(Float, default=0.0, nullable=False)
    total_amount = Column(Float, default=0.0, nullable=False)

    subscription = relationship("Subscription", back_populates="lines")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    tax_rule = relationship("TaxRule")
