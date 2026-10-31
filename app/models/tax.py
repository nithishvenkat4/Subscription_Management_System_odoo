from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from app.core.database import Base

class TaxRule(Base):
    __tablename__ = "tax_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # e.g., 'VAT 10%', 'Sales Tax 8%'
    rate = Column(Float, nullable=False, default=0.0)  # Percentage rate e.g. 10.0
    tax_type = Column(String(50), default="percentage", nullable=False)  # 'percentage', 'fixed'
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
