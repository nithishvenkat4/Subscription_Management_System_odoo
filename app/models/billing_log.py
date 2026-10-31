from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.core.database import Base

class BillingRunLog(Base):
    __tablename__ = "billing_run_logs"

    id = Column(Integer, primary_key=True, index=True)
    run_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    triggered_by = Column(String(50), default="automated_cron") # 'automated_cron' or staff email
    subscriptions_evaluated = Column(Integer, default=0)
    invoices_created = Column(Integer, default=0)
    subscriptions_skipped = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    details = Column(Text, nullable=True)
