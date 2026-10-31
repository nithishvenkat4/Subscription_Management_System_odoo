# Brightloop Software — Subscription Management System
> **One unified software platform to run plans, subscriptions, and recurring billing in one place.**

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Odoo Compatible](https://img.shields.io/badge/Odoo-17%20%7C%2018%20Compatible-714B67.svg)](https://www.odoo.com)
[![Performance SLA](https://img.shields.io/badge/Performance-%3C%202s%20SLA-brightgreen.svg)]()

---

## 🌟 Overview & Business Context

**Brightloop Software** sells software subscriptions, add-ons, and variant products ranging from small monthly business subscriptions to enterprise annual contracts. 

Prior to this system, operations were fragmented across spreadsheets, manual invoice typing, ad-hoc payment reconciliations, and quarterly reporting delays. 

This platform delivers an **end-to-end, unified solution**:
- 🔐 **Multi-Tier RBAC & Customer Portal:** Admin, Staff, and self-service Customer Portal with strict data isolation.
- 📦 **Products & Variant Surcharges:** Product catalog with customizable variants (e.g. Odoo brand adds +$560).
- 🔁 **Flexible Recurring Plans:** Daily, weekly, monthly, and yearly cadences with granular lifecycle policies (`auto_close_on_end`, `closable_early`, `pausable`, `renewable`).
- 📝 **Quotation Templates to Subscriptions:** Rapid quoting with template validity days and 5-stage subscription lifecycle (`Draft` ➔ `Quotation` ➔ `Confirmed` ➔ `Active` ➔ `Closed`).
- ⚡ **Automated Recurring Billing Engine ("Billing Day"):** High-throughput, idempotent batch invoice generator guaranteed to prevent duplicate charges or skipped cycles.
- 🏷️ **Dynamic Taxes & Automatic Discount Rules:** Fixed and percentage discounts with minimum thresholds, validity periods, and usage caps that apply automatically.
- 💳 **Payment Reconciliation & Receivables:** Multi-method payments (`Credit Card`, `Bank Transfer`, etc.) linked to invoices with real-time overdue tracking.
- 📊 **Executive Finance Analytics (< 2s SLA):** Real-time MRR, ARR, cash collected, outstanding debt, and aging overdue invoices responsive under 2 seconds across thousands of subscriptions.

---

## 🏗️ Architecture & Dual-Delivery Model

This repository provides **two complete implementations** to satisfy both standalone web application needs and enterprise ERP module requirements:

```
Subscription_Management_System_odoo/
├── app/                           # STANDALONE WEB APPLICATION PLATFORM
│   ├── api/                       # REST API Endpoints (Auth, Plans, Subs, Invoices, Analytics)
│   ├── core/                      # Config, Security (JWT, bcrypt), Database engine
│   ├── models/                    # SQLAlchemy 2.0 ORM Models
│   ├── schemas/                   # Pydantic v2 Request/Response Schemas
│   ├── services/                  # Business Logic: Billing Engine, Discount Engine, Tax Engine
│   └── static/ & templates/       # Premium Modern UI (Glassmorphic, Odoo-inspired, Responsive)
│
├── brightloop_subscription/       # NATIVE ODOO 17 / 18 ADDON MODULE
│   ├── __manifest__.py            # Odoo Module Manifest
│   ├── models/                    # Odoo ORM Models (Subscription, Plan, Line, Discount, Tax)
│   ├── views/                     # XML Views (Tree, Form, Kanban, Search, Action Menus)
│   ├── security/                  # Access Rights & Record Rules (ir.model.access.csv)
│   ├── data/                      # Automated Recurring Billing Cron & Sequences
│   └── reports/                   # QWeb Printable Invoice PDF Templates
│
├── tests/                         # AUTOMATED TEST SUITE
│   ├── test_auth.py               # Password validation & RBAC security tests
│   ├── test_billing_engine.py     # Idempotency & recurring billing cycle tests
│   ├── test_discounts.py          # Auto-application, caps, & threshold tests
│   └── test_performance.py        # 10,000 subscriptions < 2s SLA benchmark
│
├── RESEARCH_AND_ARCHITECTURE.md   # Deep architectural specification & mathematical proofs
└── README.md                      # Platform documentation & quickstart guide
```

---

## 🚀 Quickstart Guide

### 1. Requirements
- Python 3.11+
- Node.js (optional, for frontend toolchains)
- Git

### 2. Setup Virtual Environment & Install Dependencies
```bash
# Clone the repository
git clone https://github.com/nithishvenkat4/Subscription_Management_System_odoo.git
cd Subscription_Management_System_odoo

# Create virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Initialize Database & Seed Demo Data
```bash
python -m app.seed
```

### 4. Run the Web Application
```bash
python -m uvicorn app.main:app --reload --port 8000
```
Open your browser at: `http://localhost:8000`

---

## 👥 Default Demo Credentials

| Role | Email | Password | Permissions |
|---|---|---|---|
| **Administrator** | `admin@brightloop.com` | `BrightAdmin@2026` | Full system control, staff management, tax & discount rules |
| **Internal Staff** | `staff@brightloop.com` | `BrightStaff@2026` | Day-to-day quotes, subscriptions, invoices, payments |
| **Customer (Portal)** | `customer@acme.com` | `CustomerAcme@2026` | Self-service portal, view own subscriptions and invoices |

---

## 🧪 Running Automated Tests
```bash
pytest -v
```

---

## 📄 License
This project is open-source under the MIT License.
