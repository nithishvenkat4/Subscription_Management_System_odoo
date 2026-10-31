from datetime import date, timedelta
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
import app.models # Register all models
from app.models.user import User
from app.models.product import Product, ProductVariant
from app.models.plan import RecurringPlan
from app.models.tax import TaxRule
from app.models.discount import DiscountRule
from app.models.quote_template import QuotationTemplate, QuotationTemplateLine
from app.models.subscription import Subscription, SubscriptionLine
from app.models.invoice import Invoice, InvoiceLine
from app.models.payment import Payment

def seed_database():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).filter(User.email == "admin@brightloop.com").first():
            print("Database already seeded. Skipping initial seed.")
            return

        print("Seeding Users (Admin, Staff, Customers)...")
        # 1. Users
        admin_user = User(
            email="admin@brightloop.com",
            full_name="Sarah Administrator",
            hashed_password=get_password_hash("BrightAdmin@2026"),
            role="admin",
            company_name="Brightloop Software Inc.",
            phone="+1 (800) 555-0100",
            is_active=True
        )
        staff_user = User(
            email="staff@brightloop.com",
            full_name="Alex SalesRep",
            hashed_password=get_password_hash("BrightStaff@2026"),
            role="staff",
            company_name="Brightloop Software Inc.",
            phone="+1 (800) 555-0101",
            is_active=True
        )
        customer_1 = User(
            email="customer@acme.com",
            full_name="John Acme",
            hashed_password=get_password_hash("CustomerAcme@2026"),
            role="customer",
            company_name="Acme Retail Corp",
            phone="+1 (415) 555-0201",
            is_active=True
        )
        customer_2 = User(
            email="sarah@techflow.io",
            full_name="Sarah Jenkins",
            hashed_password=get_password_hash("CustomerSarah@2026"),
            role="customer",
            company_name="TechFlow Solutions",
            phone="+1 (212) 555-0202",
            is_active=True
        )
        customer_3 = User(
            email="david@globex.org",
            full_name="David Globex",
            hashed_password=get_password_hash("CustomerDavid@2026"),
            role="customer",
            company_name="Globex Enterprises",
            phone="+1 (650) 555-0203",
            is_active=True
        )
        db.add_all([admin_user, staff_user, customer_1, customer_2, customer_3])
        db.flush()

        print("Seeding Taxes...")
        # 2. Tax Rules
        tax_vat10 = TaxRule(name="VAT 10%", rate=10.0, tax_type="percentage", description="Standard Value Added Tax 10%")
        tax_sales8 = TaxRule(name="Sales Tax 8.25%", rate=8.25, tax_type="percentage", description="Regional State Sales Tax")
        tax_zero = TaxRule(name="Exempt 0%", rate=0.0, tax_type="percentage", description="Tax Exempt Customers")
        db.add_all([tax_vat10, tax_sales8, tax_zero])
        db.flush()

        print("Seeding Products and Variants...")
        # 3. Products & Variants (Specific prompt requirement: Odoo brand adds 560 to price)
        p_erp = Product(
            name="BrightERP Core Edition",
            product_type="software",
            sales_price=1200.0,
            cost_price=350.0,
            notes="Comprehensive ERP business suite with CRM, Inventory, and Accounting.",
            is_active=True
        )
        db.add(p_erp)
        db.flush()

        v_standard = ProductVariant(
            product_id=p_erp.id,
            attribute_name="Brand",
            attribute_value="Standard Edition",
            extra_price=0.0,
            sku="ERP-STD"
        )
        v_odoo = ProductVariant(
            product_id=p_erp.id,
            attribute_name="Brand",
            attribute_value="Odoo Brand Edition",
            extra_price=560.0, # Exactly from brief: "choosing the Odoo brand adds 560 to the price"
            sku="ERP-ODOO-560"
        )
        v_enterprise = ProductVariant(
            product_id=p_erp.id,
            attribute_name="Brand",
            attribute_value="Enterprise White-Label",
            extra_price=1200.0,
            sku="ERP-WHT-1200"
        )
        db.add_all([v_standard, v_odoo, v_enterprise])

        p_backup = Product(
            name="Cloud Backup & Security Suite",
            product_type="addon",
            sales_price=150.0,
            cost_price=30.0,
            notes="Hourly automated offsite backup with encryption.",
            is_active=True
        )
        p_support = Product(
            name="24/7 Dedicated Support SLA",
            product_type="service",
            sales_price=450.0,
            cost_price=120.0,
            notes="15-minute response time SLA and dedicated account manager.",
            is_active=True
        )
        p_ai = Product(
            name="AI Predictive Analytics Addon",
            product_type="addon",
            sales_price=280.0,
            cost_price=60.0,
            notes="Machine learning forecasting for revenue and stock.",
            is_active=True
        )
        db.add_all([p_backup, p_support, p_ai])
        db.flush()

        print("Seeding Recurring Plans with Lifecycle Rules...")
        # 4. Recurring Plans
        plan_monthly = RecurringPlan(
            name="Professional Monthly",
            description="Billed every month with flexible cancellation and pause support.",
            recurring_price=299.0,
            billing_interval="monthly",
            min_quantity=1,
            auto_close_on_end=False,
            closable_early=True,
            pausable=True,
            renewable=True
        )
        plan_yearly = RecurringPlan(
            name="Enterprise Yearly Contract",
            description="Annual commitment with 5-seat minimum, auto-closing upon term end.",
            recurring_price=4800.0,
            billing_interval="yearly",
            min_quantity=5,
            auto_close_on_end=True, # Closes on its own when term ends
            closable_early=False,   # Cannot be closed early
            pausable=True,
            renewable=True
        )
        plan_weekly = RecurringPlan(
            name="Agile Weekly Sprint",
            description="Weekly billing for fast-paced project teams.",
            recurring_price=89.0,
            billing_interval="weekly",
            min_quantity=1,
            auto_close_on_end=False,
            closable_early=True,
            pausable=True,
            renewable=True
        )
        plan_daily = RecurringPlan(
            name="Cloud Micro Daily",
            description="Daily rate for temporary bursts and testing environments.",
            recurring_price=15.0,
            billing_interval="daily",
            min_quantity=1,
            auto_close_on_end=True,
            closable_early=True,
            pausable=False,
            renewable=False
        )
        db.add_all([plan_monthly, plan_yearly, plan_weekly, plan_daily])
        db.flush()

        print("Seeding Discount Rules...")
        # 5. Discount Rules (Admin only feature)
        discount_seats = DiscountRule(
            name="Volume License 15% Off",
            discount_type="percentage",
            discount_value=15.0,
            min_purchase_amount=500.0,
            min_quantity=5, # Seat threshold
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() + timedelta(days=300),
            max_uses=50,
            used_count=3,
            scope="whole_subscription"
        )
        discount_startup = DiscountRule(
            name="Startup Kickoff $100 Credit",
            discount_type="fixed_amount",
            discount_value=100.0,
            min_purchase_amount=300.0,
            min_quantity=1,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=180),
            max_uses=100,
            used_count=12,
            scope="whole_subscription"
        )
        db.add_all([discount_seats, discount_startup])
        db.flush()

        print("Seeding Quotation Templates...")
        # 6. Quotation Templates
        tmpl_enterprise = QuotationTemplate(
            name="Enterprise Multi-Seat SaaS Offer",
            description="Standard quotation for enterprise accounts with Odoo Brand variant.",
            plan_id=plan_yearly.id,
            validity_days=30,
            is_active=True
        )
        db.add(tmpl_enterprise)
        db.flush()

        tmpl_line1 = QuotationTemplateLine(
            template_id=tmpl_enterprise.id,
            product_id=p_erp.id,
            variant_id=v_odoo.id,
            quantity=5,
            unit_price=1760.0 # 1200 + 560
        )
        tmpl_line2 = QuotationTemplateLine(
            template_id=tmpl_enterprise.id,
            product_id=p_backup.id,
            variant_id=None,
            quantity=1,
            unit_price=150.0
        )
        tmpl_line3 = QuotationTemplateLine(
            template_id=tmpl_enterprise.id,
            product_id=p_support.id,
            variant_id=None,
            quantity=1,
            unit_price=450.0
        )
        db.add_all([tmpl_line1, tmpl_line2, tmpl_line3])
        db.flush()

        print("Seeding Subscriptions...")
        # 7. Subscriptions across various lifecycles
        today = date.today()

        # Subscription 1: Active Enterprise subscription with Odoo Brand variant
        sub1 = Subscription(
            subscription_number="SUB-2026-00001",
            customer_id=customer_1.id,
            plan_id=plan_yearly.id,
            quotation_template_id=tmpl_enterprise.id,
            start_date=today - timedelta(days=90),
            expiry_date=today + timedelta(days=275),
            next_billing_date=today + timedelta(days=275),
            payment_terms="Net 30",
            status="active",
            auto_close_on_end=True,
            closable_early=False,
            pausable=True,
            renewable=True,
            subtotal=9400.0,
            tax_total=940.0,
            discount_total=1410.0, # 15% discount applied
            recurring_total=8930.0,
            applied_discount_id=discount_seats.id,
            notes="Enterprise annual agreement with Odoo Brand addon."
        )
        db.add(sub1)
        db.flush()

        sub1_line1 = SubscriptionLine(
            subscription_id=sub1.id,
            product_id=p_erp.id,
            variant_id=v_odoo.id,
            description="BrightERP Core Edition (Brand: Odoo Brand Edition +$560)",
            quantity=5,
            unit_price=1760.0,
            tax_id=tax_vat10.id,
            tax_rate=10.0,
            tax_amount=880.0,
            subtotal=8800.0,
            total_amount=9680.0
        )
        sub1_line2 = SubscriptionLine(
            subscription_id=sub1.id,
            product_id=p_support.id,
            variant_id=None,
            description="24/7 Dedicated Support SLA",
            quantity=1,
            unit_price=450.0,
            tax_id=tax_vat10.id,
            tax_rate=10.0,
            tax_amount=45.0,
            subtotal=450.0,
            total_amount=495.0
        )
        db.add_all([sub1_line1, sub1_line2])

        # Subscription 2: Active Monthly Subscription (due today for billing demo!)
        sub2 = Subscription(
            subscription_number="SUB-2026-00002",
            customer_id=customer_2.id,
            plan_id=plan_monthly.id,
            start_date=today - timedelta(days=30),
            expiry_date=today + timedelta(days=335),
            next_billing_date=today, # DUE TODAY!
            payment_terms="Immediate Payment",
            status="active",
            auto_close_on_end=False,
            closable_early=True,
            pausable=True,
            renewable=True,
            subtotal=1350.0,
            tax_total=135.0,
            discount_total=100.0,
            recurring_total=1385.0,
            applied_discount_id=discount_startup.id,
            notes="TechFlow monthly standard subscription."
        )
        db.add(sub2)
        db.flush()

        sub2_line = SubscriptionLine(
            subscription_id=sub2.id,
            product_id=p_erp.id,
            variant_id=v_standard.id,
            description="BrightERP Core Edition (Standard)",
            quantity=1,
            unit_price=1200.0,
            tax_id=tax_vat10.id,
            tax_rate=10.0,
            tax_amount=120.0,
            subtotal=1200.0,
            total_amount=1320.0
        )
        sub2_line2 = SubscriptionLine(
            subscription_id=sub2.id,
            product_id=p_backup.id,
            variant_id=None,
            description="Cloud Backup & Security Suite",
            quantity=1,
            unit_price=150.0,
            tax_id=tax_vat10.id,
            tax_rate=10.0,
            tax_amount=15.0,
            subtotal=150.0,
            total_amount=165.0
        )
        db.add_all([sub2_line, sub2_line2])

        # Subscription 3: Quotation Sent to Globex
        sub3 = Subscription(
            subscription_number="SUB-2026-00003",
            customer_id=customer_3.id,
            plan_id=plan_monthly.id,
            start_date=today,
            expiry_date=today + timedelta(days=365),
            next_billing_date=today,
            quote_valid_until=today + timedelta(days=14),
            payment_terms="Net 15",
            status="quotation", # Currently in Quotation state
            auto_close_on_end=False,
            closable_early=True,
            pausable=True,
            renewable=True,
            subtotal=1650.0,
            tax_total=165.0,
            discount_total=0.0,
            recurring_total=1815.0,
            notes="Sales quote delivered to David at Globex."
        )
        db.add(sub3)

        print("Seeding Invoices (Paid, Confirmed, Overdue Aging)...")
        # 8. Invoices & Aging Receivables Demonstration
        # Invoice 1: Paid invoice
        inv1 = Invoice(
            invoice_number="INV-2026-00001",
            subscription_id=sub1.id,
            customer_id=customer_1.id,
            idempotency_key=f"SUB-{sub1.id}-{(today - timedelta(days=90)).isoformat()}",
            issue_date=today - timedelta(days=90),
            due_date=today - timedelta(days=60),
            payment_terms="Net 30",
            status="paid",
            subtotal=9400.0,
            tax_amount=940.0,
            discount_amount=1410.0,
            total_amount=8930.0,
            amount_paid=8930.0, # Fully paid
            notes="Initial annual billing."
        )
        db.add(inv1)
        db.flush()

        inv1_line = InvoiceLine(
            invoice_id=inv1.id,
            product_id=p_erp.id,
            variant_id=v_odoo.id,
            description="BrightERP Core Edition (Odoo Brand +$560) x 5",
            quantity=5,
            unit_price=1760.0,
            tax_rate=10.0,
            tax_amount=880.0,
            subtotal=8800.0,
            total_amount=9680.0
        )
        db.add(inv1_line)

        # Payment for Invoice 1
        pay1 = Payment(
            payment_number="PAY-2026-00001",
            invoice_id=inv1.id,
            customer_id=customer_1.id,
            payment_method="Bank Transfer",
            amount=8930.0,
            payment_date=today - timedelta(days=75),
            transaction_reference="WIRE-US-993821",
            note="Full payment received via ACH wire."
        )
        db.add(pay1)

        # Invoice 2: 18 Days Overdue (Aging bucket 1 - 30 days)
        inv2 = Invoice(
            invoice_number="INV-2026-00002",
            subscription_id=sub2.id,
            customer_id=customer_2.id,
            idempotency_key=f"SUB-{sub2.id}-{(today - timedelta(days=30)).isoformat()}",
            issue_date=today - timedelta(days=30),
            due_date=today - timedelta(days=18), # 18 days overdue!
            payment_terms="Immediate Payment",
            status="confirmed",
            subtotal=1350.0,
            tax_amount=135.0,
            discount_amount=100.0,
            total_amount=1385.0,
            amount_paid=385.0, # Partial payment
            notes="First month subscription invoice."
        )
        db.add(inv2)
        db.flush()

        inv2_line = InvoiceLine(
            invoice_id=inv2.id,
            product_id=p_erp.id,
            variant_id=v_standard.id,
            description="BrightERP Core Edition (Standard)",
            quantity=1,
            unit_price=1200.0,
            tax_rate=10.0,
            tax_amount=120.0,
            subtotal=1200.0,
            total_amount=1320.0
        )
        db.add(inv2_line)

        # Partial Payment for Invoice 2
        pay2 = Payment(
            payment_number="PAY-2026-00002",
            invoice_id=inv2.id,
            customer_id=customer_2.id,
            payment_method="Credit Card",
            amount=385.0,
            payment_date=today - timedelta(days=15),
            transaction_reference="STRIPE-CH-38291",
            note="Partial deposit paid by credit card. Outstanding $1,000 overdue."
        )
        db.add(pay2)

        # Invoice 3: 45 Days Overdue (Aging bucket 31 - 60 days)
        inv3 = Invoice(
            invoice_number="INV-2026-00003",
            subscription_id=None,
            customer_id=customer_3.id,
            idempotency_key=None,
            issue_date=today - timedelta(days=60),
            due_date=today - timedelta(days=45), # 45 days overdue!
            payment_terms="Net 15",
            status="confirmed",
            subtotal=2400.0,
            tax_amount=240.0,
            discount_amount=0.0,
            total_amount=2640.0,
            amount_paid=0.0, # Completely unpaid
            notes="Consulting and setup invoice for Globex."
        )
        db.add(inv3)
        db.flush()

        inv3_line = InvoiceLine(
            invoice_id=inv3.id,
            product_id=p_support.id,
            description="Enterprise Custom Architecture & Setup",
            quantity=2,
            unit_price=1200.0,
            tax_rate=10.0,
            tax_amount=240.0,
            subtotal=2400.0,
            total_amount=2640.0
        )
        db.add(inv3_line)

        db.commit()
        print("Database successfully seeded with realistic business data!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
