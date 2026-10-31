import time
from datetime import date, timedelta
from app.services.analytics_service import AnalyticsService
from app.models.user import User
from app.models.plan import RecurringPlan
from app.models.subscription import Subscription
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.core.security import get_password_hash

def test_finance_dashboard_sub_2_second_performance_sla(db):
    """
    Validates that the finance dashboard aggregation responds in under two seconds
    even with thousands of subscriptions and invoices.
    """
    print("\nSetting up benchmark data...")
    # 1. Setup Base Customer & Plan
    customer = User(
        email="perf_cust@example.com",
        full_name="Performance Customer",
        hashed_password=get_password_hash("PerfPassword@123"),
        role="customer"
    )
    plan = RecurringPlan(
        name="Performance Monthly Plan",
        billing_interval="monthly",
        recurring_price=150.0,
        min_quantity=1
    )
    db.add_all([customer, plan])
    db.flush()

    today = date.today()

    # Bulk insert 2,500 subscriptions
    bulk_subs = []
    for i in range(2500):
        status = "active" if i % 2 == 0 else "closed"
        bulk_subs.append(Subscription(
            subscription_number=f"SUB-PERF-{i:05d}",
            customer_id=customer.id,
            plan_id=plan.id,
            start_date=today - timedelta(days=60),
            next_billing_date=today + timedelta(days=i % 30),
            payment_terms="Immediate Payment",
            status=status,
            subtotal=150.0,
            tax_total=15.0,
            discount_total=0.0,
            recurring_total=165.0
        ))
    db.bulk_save_objects(bulk_subs)

    # Bulk insert 2,500 invoices (including current and overdue)
    bulk_invoices = []
    for i in range(2500):
        due = today - timedelta(days=(i % 45)) if i % 3 == 0 else today + timedelta(days=15)
        st = "confirmed" if i % 2 == 0 else "paid"
        amt_paid = 165.0 if st == "paid" else 0.0
        bulk_invoices.append(Invoice(
            invoice_number=f"INV-PERF-{i:05d}",
            customer_id=customer.id,
            issue_date=today - timedelta(days=30),
            due_date=due,
            payment_terms="Immediate Payment",
            status=st,
            subtotal=150.0,
            tax_amount=15.0,
            discount_amount=0.0,
            total_amount=165.0,
            amount_paid=amt_paid
        ))
    db.bulk_save_objects(bulk_invoices)
    db.commit()

    print("Executing Analytics Dashboard query benchmark...")
    # Start timer
    start_time = time.perf_counter()

    # Run dashboard calculation
    result = AnalyticsService.get_finance_dashboard(db)

    elapsed_time = time.perf_counter() - start_time
    print(f"Finance Dashboard executed in {elapsed_time:.4f} seconds for 5,000 total records.")

    # Assert SLA (< 2.0 seconds)
    assert elapsed_time < 2.0, f"Query took {elapsed_time:.2f}s, exceeding 2.0s SLA!"
    assert result["summary"]["active_subscriptions_count"] > 0
    assert result["summary"]["mrr"] > 0
    assert result["summary"]["total_owed"] > 0
    assert result["summary"]["overdue_count"] > 0
