from datetime import date, timedelta
from app.services.billing_engine import BillingEngine
from app.services.payment_service import PaymentService
from app.models.user import User
from app.models.product import Product, ProductVariant
from app.models.plan import RecurringPlan
from app.models.tax import TaxRule
from app.models.subscription import Subscription, SubscriptionLine
from app.models.invoice import Invoice
from app.core.security import get_password_hash

def test_automated_billing_and_zero_duplicate_guarantee(db):
    # Setup test customer
    customer = User(
        email="billing_test@example.com",
        full_name="Billing Customer",
        hashed_password=get_password_hash("TestPassword@123"),
        role="customer"
    )
    db.add(customer)

    # Setup Plan & Tax
    plan = RecurringPlan(
        name="Test Monthly Plan",
        billing_interval="monthly",
        recurring_price=200.0,
        min_quantity=1,
        auto_close_on_end=False
    )
    tax = TaxRule(name="VAT 10%", rate=10.0, tax_type="percentage")
    prod = Product(name="Cloud SaaS", sales_price=200.0, cost_price=50.0)
    db.add_all([plan, tax, prod])
    db.flush()

    # Setup Active Subscription Due Today
    today = date.today()
    sub = Subscription(
        subscription_number="SUB-TEST-001",
        customer_id=customer.id,
        plan_id=plan.id,
        start_date=today - timedelta(days=30),
        next_billing_date=today, # Due today!
        payment_terms="Immediate Payment",
        status="active",
        auto_close_on_end=False,
        subtotal=200.0,
        tax_total=20.0,
        recurring_total=220.0
    )
    db.add(sub)
    db.flush()

    sline = SubscriptionLine(
        subscription_id=sub.id,
        product_id=prod.id,
        description="Cloud SaaS Seat",
        quantity=1,
        unit_price=200.0,
        tax_id=tax.id,
        tax_rate=10.0,
        tax_amount=20.0,
        subtotal=200.0,
        total_amount=220.0
    )
    db.add(sline)
    db.commit()

    # 1. Run Billing Engine on Billing Day
    result1 = BillingEngine.run_recurring_billing(db, target_date=today, triggered_by="test_run_1")
    assert result1["evaluated"] == 1
    assert result1["created"] == 1
    assert result1["skipped"] == 0

    # Verify invoice was created
    inv = db.query(Invoice).filter(Invoice.subscription_id == sub.id).first()
    assert inv is not None
    assert inv.status == "draft"
    assert inv.subtotal == 200.0
    assert inv.tax_amount == 20.0
    assert inv.total_amount == 220.0
    assert inv.outstanding_amount == 220.0

    # Verify next_billing_date was advanced forward by 1 month
    db.refresh(sub)
    assert sub.next_billing_date > today

    # 2. Re-run Billing Engine on same date: ZERO DOUBLE BILLING GUARANTEE
    # If called again with the same target date, it must NOT bill again
    result2 = BillingEngine.run_recurring_billing(db, target_date=today, triggered_by="test_run_2")
    assert result2["created"] == 0
    assert db.query(Invoice).filter(Invoice.subscription_id == sub.id).count() == 1

def test_payment_recording_and_auto_reconciliation(db):
    customer = User(
        email="payment_test@example.com",
        full_name="Payment Customer",
        hashed_password=get_password_hash("TestPassword@123"),
        role="customer"
    )
    db.add(customer)
    db.flush()

    inv = Invoice(
        invoice_number="INV-PAY-001",
        customer_id=customer.id,
        issue_date=date.today(),
        due_date=date.today(),
        payment_terms="Immediate Payment",
        status="confirmed",
        subtotal=500.0,
        tax_amount=50.0,
        total_amount=550.0,
        amount_paid=0.0
    )
    db.add(inv)
    db.commit()

    # Partial payment
    pay1 = PaymentService.record_payment(
        db=db,
        invoice_id=inv.id,
        amount=200.0,
        payment_method="Credit Card",
        transaction_reference="CC-101"
    )
    db.refresh(inv)
    assert inv.amount_paid == 200.0
    assert inv.outstanding_amount == 350.0
    assert inv.status == "confirmed" # still confirmed, not paid

    # Full remaining balance payment
    pay2 = PaymentService.record_payment(
        db=db,
        invoice_id=inv.id,
        amount=350.0,
        payment_method="Bank Transfer",
        transaction_reference="WIRE-202"
    )
    db.refresh(inv)
    assert inv.amount_paid == 550.0
    assert inv.outstanding_amount == 0.0
    assert inv.status == "paid" # Automatically marked PAID!
