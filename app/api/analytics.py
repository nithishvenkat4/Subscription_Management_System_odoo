from datetime import date
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.services.analytics_service import AnalyticsService
from app.api.deps import get_current_staff_or_admin

router = APIRouter(prefix="/analytics", tags=["Finance & Executive Reporting"])

@router.get("/dashboard")
def get_finance_dashboard(
    date_from: Optional[date] = Query(None, description="Start date for revenue aggregation"),
    date_to: Optional[date] = Query(None, description="End date for revenue aggregation"),
    customer_id: Optional[int] = Query(None, description="Filter by customer"),
    plan_id: Optional[int] = Query(None, description="Filter by plan"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_staff_or_admin)
) -> Dict[str, Any]:
    """
    Finance Lead Executive Dashboard (< 2s Performance SLA).
    Provides:
    - Active Subscriptions count
    - Normalized MRR & ARR
    - Total Revenue Collected in period
    - Total Accounts Receivable Owed
    - Overdue Invoices breakdown & Aging analysis (1-30, 31-60, 60+ days)
    - Plan distribution breakdown
    - Recent payments ledger
    """
    return AnalyticsService.get_finance_dashboard(
        db=db,
        date_from=date_from,
        date_to=date_to,
        customer_id=customer_id,
        plan_id=plan_id
    )
