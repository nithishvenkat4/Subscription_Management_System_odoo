from datetime import datetime, date, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_number = Column(String(50), unique=True, index=True, nullable=False) # e.g. PAY-2026-0001
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Method: 'Credit Card', 'Bank Transfer', 'Stripe', 'Cash', 'Cheque'
    payment_method = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False, default=date.today, index=True)
    transaction_reference = Column(String(100), nullable=True)
    note = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    invoice = relationship("Invoice", back_populates="payments")
    customer = relationship("User", back_populates="payments", foreign_keys=[customer_id])
    created_by = relationship("User", foreign_keys=[created_by_id])

    __table_args__ = (
        Index("idx_pay_date_inv", "payment_date", "invoice_id"),
    )
