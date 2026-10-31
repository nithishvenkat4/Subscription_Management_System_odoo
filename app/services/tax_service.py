from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models.tax import TaxRule

class TaxService:

    @staticmethod
    def get_tax_rule(db: Session, tax_id: Optional[int]) -> Optional[TaxRule]:
        if not tax_id:
            return None
        return db.query(TaxRule).filter(TaxRule.id == tax_id, TaxRule.is_active == True).first()

    @staticmethod
    def calculate_line_tax(tax_rule: Optional[TaxRule], subtotal: float) -> Tuple[float, float]:
        """
        Calculates (tax_rate, tax_amount) for a given line subtotal.
        """
        if not tax_rule or not tax_rule.is_active:
            return 0.0, 0.0

        if tax_rule.tax_type == "percentage":
            tax_amount = round(subtotal * (tax_rule.rate / 100.0), 2)
            return tax_rule.rate, tax_amount
        elif tax_rule.tax_type == "fixed":
            return tax_rule.rate, round(tax_rule.rate, 2)
        return 0.0, 0.0
