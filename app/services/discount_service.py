from datetime import date
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from app.models.discount import DiscountRule

class DiscountService:

    @staticmethod
    def get_eligible_discount(
        db: Session,
        subtotal: float,
        total_quantity: int,
        target_product_ids: List[int],
        discount_id: Optional[int] = None
    ) -> Optional[Tuple[DiscountRule, float]]:
        """
        Evaluates discount eligibility based on Brightloop rules:
        - Must be active
        - Today within start_date and end_date (if set)
        - used_count < max_uses (if set)
        - subtotal >= min_purchase_amount
        - total_quantity >= min_quantity
        - product scope matching (if scope is 'specific_products')
        Returns (DiscountRule, calculated_discount_amount) or None.
        """
        today = date.today()

        if discount_id:
            rules = db.query(DiscountRule).filter(DiscountRule.id == discount_id, DiscountRule.is_active == True).all()
        else:
            rules = db.query(DiscountRule).filter(DiscountRule.is_active == True).all()

        for rule in rules:
            # Check dates
            if rule.start_date and today < rule.start_date:
                continue
            if rule.end_date and today > rule.end_date:
                continue

            # Check usage limit
            if rule.max_uses is not None and rule.used_count >= rule.max_uses:
                continue

            # Check minimum purchase amount
            if subtotal < rule.min_purchase_amount:
                continue

            # Check minimum quantity
            if total_quantity < rule.min_quantity:
                continue

            # Check scope
            if rule.scope == "specific_products" and rule.product_id:
                if rule.product_id not in target_product_ids:
                    continue

            # Calculate discount value
            if rule.discount_type == "percentage":
                discount_amount = round(subtotal * (rule.discount_value / 100.0), 2)
            else: # fixed_amount
                discount_amount = min(subtotal, round(rule.discount_value, 2))

            return rule, discount_amount

        return None

    @staticmethod
    def record_discount_application(db: Session, discount_rule: DiscountRule) -> None:
        """
        Increments usage counter and deactivates if ceiling reached.
        """
        discount_rule.used_count += 1
        if discount_rule.max_uses is not None and discount_rule.used_count >= discount_rule.max_uses:
            discount_rule.is_active = False
        db.commit()
