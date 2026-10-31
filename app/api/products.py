from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.product import Product, ProductVariant
from app.models.user import User
from app.schemas.product import ProductCreate, ProductResponse, ProductVariantCreate, ProductVariantResponse
from app.api.deps import get_current_user, get_current_admin

router = APIRouter(prefix="/products", tags=["Products & Variants"])

@router.get("", response_model=List[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    """
    List all active products and their variants.
    """
    return db.query(Product).filter(Product.is_active == True).all()

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Admin-only: Create a new product with optional initial variants.
    """
    product = Product(
        name=payload.name,
        product_type=payload.product_type,
        sales_price=payload.sales_price,
        cost_price=payload.cost_price,
        notes=payload.notes,
        is_active=payload.is_active
    )
    db.add(product)
    db.flush()

    if payload.variants:
        for v in payload.variants:
            variant = ProductVariant(
                product_id=product.id,
                attribute_name=v.attribute_name,
                attribute_value=v.attribute_value,
                extra_price=v.extra_price,
                sku=v.sku,
                is_active=v.is_active
            )
            db.add(variant)

    db.commit()
    db.refresh(product)
    return product

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product

@router.post("/{product_id}/variants", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED)
def add_product_variant(
    product_id: int,
    payload: ProductVariantCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Admin-only: Add a variant with price surcharge (e.g., Brand: Odoo +560).
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    variant = ProductVariant(
        product_id=product.id,
        attribute_name=payload.attribute_name,
        attribute_value=payload.attribute_value,
        extra_price=payload.extra_price,
        sku=payload.sku,
        is_active=payload.is_active
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant
