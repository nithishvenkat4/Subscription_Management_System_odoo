{
    "name": "Brightloop Subscription Management System",
    "version": "17.0.1.0.0",
    "category": "Sales/Subscriptions",
    "summary": "Unified platform to run plans, subscriptions, and automated recurring billing.",
    "description": """
Brightloop Software — Subscription Management System
=====================================================
Built for Odoo 17 & 18.
- Multi-tier recurring plans (daily, weekly, monthly, yearly)
- Granular lifecycle control (auto-close, early close, pausable, renewable)
- Quotation templates to subscription generation
- Automated recurring billing engine with zero double billing
- Admin discount rules engine with seat thresholds and usage caps
- Product variant surcharges (e.g. Odoo brand +560)
- End-of-month finance analytics and accounts receivable tracking
    """,
    "author": "Brightloop Software / Antigravity AI",
    "website": "https://github.com/nithishvenkat4/Subscription_Management_System_odoo",
    "depends": ["base", "sale", "account"],
    "data": [
        "security/brightloop_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/ir_cron_data.xml",
        "views/plan_views.xml",
        "views/subscription_views.xml",
        "views/discount_rule_views.xml",
        "views/product_views.xml",
        "views/menu_views.xml"
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3"
}
