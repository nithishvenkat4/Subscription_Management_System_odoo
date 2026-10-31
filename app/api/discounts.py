from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.discount import DiscountRule
from app.models.user import User
from app.schemas.discount import DiscountRuleCreate, DiscountRuleResponse
from app.api.deps import get_current_user, get_current_admin

router = APIRouter(prefix="/discounts", tags=["Discount Rules"])

@router.get("", response_model=List[DiscountRuleResponse])
def list_discount_rules(db: Session = Depends(get_db)):
    """
    List discount rules.
    """
    return db.query(DiscountRule).filter(DiscountRule.is_active == True).all()

@router.post("", response_model=DiscountRuleResponse, status_code=status.HTTP_201_CREATED)
def create_discount_rule(
    payload: DiscountRuleCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Admin-only: Create an automatic discount rule with quantity thresholds,
    usage ceilings, date limits, and scope.
    """
    rule = DiscountRule(
        name=payload.name,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        min_purchase_amount=payload.min_purchase_amount,
        min_quantity=payload.min_quantity,
        start_date=payload.start_date,
        end_date=payload.end_date,
        max_uses=payload.max_uses,
        scope=payload.scope,
        product_id=payload.product_id,
        is_active=payload.is_active
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

@router.get("/{discount_id}", response_model=DiscountRuleResponse)
def get_discount_rule(discount_id: int, db: Session = Depends(get_db)):
    rule = db.query(DiscountRule).filter(DiscountRule.id == discount_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Discount rule not found.")
    return rule
