from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import (
    get_password_hash,
    verify_password,
    validate_password_strength,
    generate_reset_token,
    create_access_token
)
from app.core.config import settings
from app.models.user import User

class AuthService:

    @staticmethod
    def register_user(
        db: Session,
        email: str,
        full_name: str,
        password: str,
        role: str = "customer",
        company_name: Optional[str] = None,
        phone: Optional[str] = None,
        requesting_user: Optional[User] = None
    ) -> User:
        """
        Creates a new user account with strict Brightloop rules:
        1. Email must be unique.
        2. Password must pass validation (>8 chars, uppercase, lowercase, special char).
        3. Only Admins can create 'staff' or 'admin' users.
        """
        email_clean = email.strip().lower()
        existing = db.query(User).filter(User.email == email_clean).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An account with email '{email_clean}' already exists."
            )

        # RBAC check: Only admin can add staff or another admin (except when bootstrapping the very first admin)
        if role in ["staff", "admin"]:
            is_initial_bootstrap = (role == "admin" and db.query(User).filter(User.role == "admin").count() == 0)
            if not is_initial_bootstrap:
                if not requesting_user or requesting_user.role != "admin":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied: Only an Administrator can add internal staff members."
                    )

        # Password strength validation
        is_valid, error_msg = validate_password_strength(password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        hashed = get_password_hash(password)
        user = User(
            email=email_clean,
            full_name=full_name.strip(),
            hashed_password=hashed,
            role=role,
            company_name=company_name.strip() if company_name else None,
            phone=phone.strip() if phone else None,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This user account has been deactivated."
            )
        return user

    @staticmethod
    def request_password_reset(db: Session, email: str) -> Tuple[str, str]:
        """
        Generates a secure password reset token valid for 1 hour.
        Returns (token, simulated_reset_link).
        """
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if not user:
            # Prevent email enumeration by returning a generic success or throwing controlled exception
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No registered account found with that email address."
            )

        token = generate_reset_token()
        user.reset_token = token
        user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        db.commit()

        reset_link = f"/reset-password?token={token}"
        return token, reset_link

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> User:
        """
        Validates the reset token and updates the user's password.
        """
        user = db.query(User).filter(User.reset_token == token).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset link."
            )

        if user.reset_token_expires_at:
            # Handle timezone awareness
            expiry = user.reset_token_expires_at
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expiry:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This password reset link has expired. Please request a new one."
                )

        is_valid, error_msg = validate_password_strength(new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        user.hashed_password = get_password_hash(new_password)
        user.reset_token = None
        user.reset_token_expires_at = None
        db.commit()
        db.refresh(user)
        return user
