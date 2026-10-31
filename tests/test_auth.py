import pytest
from app.core.security import validate_password_strength
from app.services.auth_service import AuthService
from app.models.user import User

def test_password_strength_validation():
    # Less than or equal to 8 characters
    valid, msg = validate_password_strength("Pass@1")
    assert not valid
    assert "more than 8 characters" in msg

    # Missing uppercase
    valid, msg = validate_password_strength("lowercase@123")
    assert not valid
    assert "uppercase" in msg

    # Missing lowercase
    valid, msg = validate_password_strength("UPPERCASE@123")
    assert not valid
    assert "lowercase" in msg

    # Missing special character
    valid, msg = validate_password_strength("NoSpecialChar123")
    assert not valid
    assert "special character" in msg

    # Valid password
    valid, msg = validate_password_strength("BrightAdmin@2026")
    assert valid
    assert msg is None

def test_customer_registration_unique_email(db):
    user1 = AuthService.register_user(
        db=db,
        email="test_user@example.com",
        full_name="Test Customer",
        password="ValidPassword@123",
        role="customer"
    )
    assert user1.id is not None
    assert user1.email == "test_user@example.com"
    assert user1.role == "customer"

    # Duplicate email should raise HTTPException 400
    with pytest.raises(Exception) as excinfo:
        AuthService.register_user(
            db=db,
            email="test_user@example.com",
            full_name="Duplicate User",
            password="ValidPassword@123",
            role="customer"
        )
    assert "already exists" in str(excinfo.value)

def test_rbac_only_admin_can_add_staff(db):
    admin = AuthService.register_user(
        db=db,
        email="admin_test@brightloop.com",
        full_name="Admin Boss",
        password="AdminPassword@2026",
        role="admin"
    )
    customer = AuthService.register_user(
        db=db,
        email="cust_test@example.com",
        full_name="Customer Normal",
        password="CustomerPass@2026",
        role="customer"
    )

    # Customer trying to add staff should fail
    with pytest.raises(Exception) as excinfo:
        AuthService.register_user(
            db=db,
            email="new_staff1@brightloop.com",
            full_name="Staff One",
            password="StaffPassword@2026",
            role="staff",
            requesting_user=customer
        )
    assert "Only an Administrator" in str(excinfo.value)

    # Admin adding staff should succeed
    staff = AuthService.register_user(
        db=db,
        email="new_staff2@brightloop.com",
        full_name="Staff Two",
        password="StaffPassword@2026",
        role="staff",
        requesting_user=admin
    )
    assert staff.id is not None
    assert staff.role == "staff"

def test_password_reset_flow(db):
    user = AuthService.register_user(
        db=db,
        email="reset_target@example.com",
        full_name="Reset Target",
        password="OldPassword@123",
        role="customer"
    )

    token, link = AuthService.request_password_reset(db=db, email=user.email)
    assert token is not None
    assert f"token={token}" in link

    # Reset with valid new password
    updated_user = AuthService.reset_password(db=db, token=token, new_password="NewSecurePass@2026")
    assert updated_user.reset_token is None

    # Authenticate with new password
    auth_user = AuthService.authenticate_user(db=db, email="reset_target@example.com", password="NewSecurePass@2026")
    assert auth_user.id == user.id
