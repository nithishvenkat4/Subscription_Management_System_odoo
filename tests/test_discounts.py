from datetime import date, timedelta
from app.services.discount_service import DiscountService
from app.models.discount import DiscountRule

def test_discount_eligibility_and_seat_threshold(db):
    rule = DiscountRule(
        name="High Seat 20% Off",
        discount_type="percentage",
        discount_value=20.0,
        min_purchase_amount=500.0,
        min_quantity=5, # Requires at least 5 seats!
        max_uses=10,
        used_count=0,
        scope="whole_subscription",
        is_active=True
    )
    db.add(rule)
    db.commit()

    # Case 1: Below seat threshold (3 seats, total $600) -> Ineligible!
    eval1 = DiscountService.get_eligible_discount(
        db=db,
        subtotal=600.0,
        total_quantity=3, # Less than 5
        target_product_ids=[1],
        discount_id=rule.id
    )
    assert eval1 is None

    # Case 2: Above seat threshold (5 seats, total $600) -> Eligible!
    eval2 = DiscountService.get_eligible_discount(
        db=db,
        subtotal=600.0,
        total_quantity=5,
        target_product_ids=[1],
        discount_id=rule.id
    )
    assert eval2 is not None
    r, amt = eval2
    assert r.id == rule.id
    assert amt == 120.0 # 20% of 600

def test_discount_usage_ceiling_and_auto_deactivation(db):
    rule = DiscountRule(
        name="Flash $50 Off",
        discount_type="fixed_amount",
        discount_value=50.0,
        min_purchase_amount=100.0,
        min_quantity=1,
        max_uses=2, # Can only be used 2 times!
        used_count=0,
        scope="whole_subscription",
        is_active=True
    )
    db.add(rule)
    db.commit()

    # Use 1
    DiscountService.record_discount_application(db, rule)
    assert rule.used_count == 1
    assert rule.is_active is True

    # Use 2 -> reaches ceiling
    DiscountService.record_discount_application(db, rule)
    assert rule.used_count == 2
    assert rule.is_active is False # Automatically deactivated!

    # Next attempt should be ineligible
    eval_exhausted = DiscountService.get_eligible_discount(
        db=db,
        subtotal=200.0,
        total_quantity=1,
        target_product_ids=[],
        discount_id=rule.id
    )
    assert eval_exhausted is None
