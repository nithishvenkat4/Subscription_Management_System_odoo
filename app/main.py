import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import engine, Base, get_db
import app.models  # Ensure all models are registered
from app.api import (
    auth,
    products,
    plans,
    taxes,
    discounts,
    quote_templates,
    subscriptions,
    invoices,
    payments,
    analytics
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Unified platform for subscription lifecycle, recurring billing, and finance analytics.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static and Templates
os.makedirs("app/static", exist_ok=True)
os.makedirs("app/templates", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Register API routers under /api/v1
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(products.router, prefix=settings.API_V1_STR)
app.include_router(plans.router, prefix=settings.API_V1_STR)
app.include_router(taxes.router, prefix=settings.API_V1_STR)
app.include_router(discounts.router, prefix=settings.API_V1_STR)
app.include_router(quote_templates.router, prefix=settings.API_V1_STR)
app.include_router(subscriptions.router, prefix=settings.API_V1_STR)
app.include_router(invoices.router, prefix=settings.API_V1_STR)
app.include_router(payments.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)

@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": settings.PROJECT_NAME})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "title": "Sign In — Brightloop Software"})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "title": "Create Account — Brightloop Software"})

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request):
    return templates.TemplateResponse("reset_password.html", {"request": request, "title": "Reset Password — Brightloop Software"})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "title": "Finance Lead Dashboard — Brightloop Software"})

@app.get("/subscriptions-view", response_class=HTMLResponse)
async def subscriptions_page(request: Request):
    return templates.TemplateResponse("subscriptions.html", {"request": request, "title": "Subscriptions & Quotes — Brightloop"})

@app.get("/invoices-view", response_class=HTMLResponse)
async def invoices_page(request: Request):
    return templates.TemplateResponse("invoices.html", {"request": request, "title": "Invoices & Billing Day — Brightloop"})

@app.get("/payments-view", response_class=HTMLResponse)
async def payments_page(request: Request):
    return templates.TemplateResponse("payments.html", {"request": request, "title": "Payments & Reconciliation — Brightloop"})

@app.get("/catalog-view", response_class=HTMLResponse)
async def catalog_page(request: Request):
    return templates.TemplateResponse("catalog.html", {"request": request, "title": "Products, Plans & Discounts — Brightloop"})

@app.get("/portal", response_class=HTMLResponse)
async def customer_portal_page(request: Request):
    return templates.TemplateResponse("portal.html", {"request": request, "title": "Customer Self-Service Portal — Brightloop"})

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Brightloop Software Subscription Engine", "version": settings.VERSION}
