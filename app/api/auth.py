from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    StaffCreate,
    UserLogin,
    PasswordResetRequest,
    PasswordResetConfirm,
    UserResponse,
    TokenResponse
)
from app.services.auth_service import AuthService
from app.api.deps import get_current_user, get_current_admin

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_customer(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Customer self-registration with Brightloop password requirements:
    > 8 chars, 1 uppercase, 1 lowercase, 1 special char.
    """
    user = AuthService.register_user(
        db=db,
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
        role="customer",
        company_name=payload.company_name,
        phone=payload.phone
    )
    return user

@router.post("/register-staff", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_staff(
    payload: StaffCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Admin-only endpoint to add a new internal staff member.
    """
    user = AuthService.register_user(
        db=db,
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
        role="staff",
        company_name=payload.company_name,
        phone=payload.phone,
        requesting_user=admin
    )
    return user

@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, response: Response, db: Session = Depends(get_db)):
    """
    Authenticates user and returns JWT token.
    """
    user = AuthService.authenticate_user(db=db, email=payload.email, password=payload.password)
    access_token = create_access_token(data={"sub": user.email, "role": user.role, "id": user.id})
    
    # Also set http-only cookie for easy browser UI navigation
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="lax",
        max_age=86400
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out."}

@router.post("/forgot-password")
def forgot_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Generates password reset link for registered email.
    """
    token, reset_link = AuthService.request_password_reset(db=db, email=payload.email)
    return {
        "message": "Password reset link has been dispatched to your registered email.",
        "simulated_reset_link": reset_link,
        "token": token
    }

@router.post("/reset-password", response_model=UserResponse)
def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    Validates token and updates user password.
    """
    user = AuthService.reset_password(db=db, token=payload.token, new_password=payload.new_password)
    return user

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/staff", response_model=List[UserResponse])
def list_staff(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return db.query(User).filter(User.role.in_(["staff", "admin"])).all()

@router.get("/customers", response_model=List[UserResponse])
def list_customers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == "customer":
        return [current_user]
    return db.query(User).filter(User.role == "customer").all()
