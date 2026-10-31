from datetime import datetime, date, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, index=True, nullable=False) # e.g. INV-2026-0001
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Billing Cycle Protection (Idempotency Key: prevents duplicate billing)
    idempotency_key = Column(String(100), unique=True, nullable=True, index=True)
    
    issue_date = Column(Date, nullable=False, default=date.today)
    due_date = Column(Date, nullable=False, index=True)
    payment_terms = Column(String(100), default="Immediate Payment", nullable=False)
    
    # Status Machine: 'draft' -> 'confirmed' -> 'paid' (also 'cancelled')
    status = Column(String(50), default="draft", nullable=False, index=True)
    
    # Financial Totals
    subtotal = Column(Float, default=0.0, nullable=False)
    tax_amount = Column(Float, default=0.0, nullable=False)
    discount_amount = Column(Float, default=0.0, nullable=False)
    total_amount = Column(Float, default=0.0, nullable=False)
    amount_paid = Column(Float, default=0.0, nullable=False)
    
    notes = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True) # When invoice was emailed/dispatched
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    customer = relationship("User", back_populates="invoices", foreign_keys=[customer_id])
    subscription = relationship("Subscription", back_populates="invoices")
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice")

    # Composite Index for Sub-2-Second Query SLA
    __table_args__ = (
        Index("idx_inv_status_due", "status", "due_date"),
        Index("idx_inv_cust_status", "customer_id", "status"),
    )

    @property
    def outstanding_amount(self) -> float:
        return max(0.0, round(self.total_amount - self.amount_paid, 2))

    @property
    def is_overdue(self) -> bool:
        if self.status in ["paid", "cancelled"]:
            return False
        return self.due_date < date.today() and self.outstanding_amount > 0

class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)
    description = Column(String(255), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Float, default=0.0, nullable=False)
    tax_rate = Column(Float, default=0.0, nullable=False)
    tax_amount = Column(Float, default=0.0, nullable=False)
    discount_amount = Column(Float, default=0.0, nullable=False)
    subtotal = Column(Float, default=0.0, nullable=False)
    total_amount = Column(Float, default=0.0, nullable=False)

    invoice = relationship("Invoice", back_populates="lines")
    product = relationship("Product")
    variant = relationship("ProductVariant")
