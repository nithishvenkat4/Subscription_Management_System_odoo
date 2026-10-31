from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.plan import RecurringPlan
from app.models.user import User
from app.schemas.plan import PlanCreate, PlanResponse
from app.api.deps import get_current_user, get_current_admin

router = APIRouter(prefix="/plans", tags=["Recurring Plans"])

@router.get("", response_model=List[PlanResponse])
def list_plans(db: Session = Depends(get_db)):
    """
    List all active subscription plans.
    """
    return db.query(RecurringPlan).filter(RecurringPlan.is_active == True).all()

@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    payload: PlanCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Admin-only: Configure a new recurring plan with billing interval and lifecycle rules:
    - billing_interval: daily, weekly, monthly, yearly
    - min_quantity
    - available_from & available_to
    - auto_close_on_end, closable_early, pausable, renewable
    """
    plan = RecurringPlan(
        name=payload.name,
        description=payload.description,
        recurring_price=payload.recurring_price,
        billing_interval=payload.billing_interval,
        min_quantity=payload.min_quantity,
        available_from=payload.available_from,
        available_to=payload.available_to,
        auto_close_on_end=payload.auto_close_on_end,
        closable_early=payload.closable_early,
        pausable=payload.pausable,
        renewable=payload.renewable,
        is_active=payload.is_active
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan

@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(RecurringPlan).filter(RecurringPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")
    return plan
