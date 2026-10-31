from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class RecurringPlan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    recurring_price = Column(Float, default=0.0, nullable=False)
    billing_interval = Column(String(50), nullable=False, default="monthly")  # 'daily', 'weekly', 'monthly', 'yearly'
    min_quantity = Column(Integer, default=1, nullable=False)
    available_from = Column(Date, nullable=True)
    available_to = Column(Date, nullable=True)
    
    # Plan Lifecycle Flags (Admin controlled)
    auto_close_on_end = Column(Boolean, default=False)
    closable_early = Column(Boolean, default=True)
    pausable = Column(Boolean, default=True)
    renewable = Column(Boolean, default=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    subscriptions = relationship("Subscription", back_populates="plan")
    quotation_templates = relationship("QuotationTemplate", back_populates="plan")
