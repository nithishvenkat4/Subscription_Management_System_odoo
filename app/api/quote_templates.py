from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.quote_template import QuotationTemplate, QuotationTemplateLine
from app.models.product import Product, ProductVariant
from app.models.user import User
from app.schemas.quote_template import (
    QuotationTemplateCreate,
    QuotationTemplateResponse,
    QuotationTemplateLineCreate
)
from app.api.deps import get_current_user, get_current_staff_or_admin

router = APIRouter(prefix="/quotation-templates", tags=["Quotation Templates"])

@router.get("", response_model=List[QuotationTemplateResponse])
def list_quotation_templates(db: Session = Depends(get_db)):
    return db.query(QuotationTemplate).filter(QuotationTemplate.is_active == True).all()

@router.post("", response_model=QuotationTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_quotation_template(
    payload: QuotationTemplateCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_staff_or_admin)
):
    """
    Staff/Admin: Create pre-configured quotation template with lines and validity days.
    """
    template = QuotationTemplate(
        name=payload.name,
        description=payload.description,
        plan_id=payload.plan_id,
        validity_days=payload.validity_days,
        is_active=payload.is_active
    )
    db.add(template)
    db.flush()

    if payload.lines:
        for line in payload.lines:
            # If unit_price not specified, compute from product + variant surcharge
            unit_price = line.unit_price
            if unit_price is None:
                prod = db.query(Product).filter(Product.id == line.product_id).first()
                base_price = prod.sales_price if prod else 0.0
                extra = 0.0
                if line.variant_id:
                    var = db.query(ProductVariant).filter(ProductVariant.id == line.variant_id).first()
                    extra = var.extra_price if var else 0.0
                unit_price = base_price + extra

            tline = QuotationTemplateLine(
                template_id=template.id,
                product_id=line.product_id,
                variant_id=line.variant_id,
                quantity=line.quantity,
                unit_price=unit_price
            )
            db.add(tline)

    db.commit()
    db.refresh(template)
    return template

@router.get("/{template_id}", response_model=QuotationTemplateResponse)
def get_quotation_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(QuotationTemplate).filter(QuotationTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Quotation template not found.")
    return template
