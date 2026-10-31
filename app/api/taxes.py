from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.tax import TaxRule
from app.models.user import User
from app.schemas.tax import TaxRuleCreate, TaxRuleResponse
from app.api.deps import get_current_user, get_current_admin

router = APIRouter(prefix="/taxes", tags=["Tax Rules"])

@router.get("", response_model=List[TaxRuleResponse])
def list_tax_rules(db: Session = Depends(get_db)):
    return db.query(TaxRule).filter(TaxRule.is_active == True).all()

@router.post("", response_model=TaxRuleResponse, status_code=status.HTTP_201_CREATED)
def create_tax_rule(
    payload: TaxRuleCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Admin-only: Create a tax calculation rule.
    """
    rule = TaxRule(
        name=payload.name,
        rate=payload.rate,
        tax_type=payload.tax_type,
        description=payload.description,
        is_active=payload.is_active
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule
