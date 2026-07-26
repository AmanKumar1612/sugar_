import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_email_token,
    create_password_reset_token,
    verify_token,
    verify_refresh_token,
    is_verify_token,
    is_reset_token,
    is_refresh_token,
)
from app.models.user import User
from app.models.role import Role
from app.repositories.user_repository import UserRepository
from app.repositories.password_reset_repository import PasswordResetRepository
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    ForgotPasswordRequest,
    AuthResponse,
    GoogleLoginRequest,
    RefreshTokenRequest,
    UserResponse,
    ResetPasswordRequest,
)
from app.services.google_auth import GoogleAuthService
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def _build_auth_response(user: User) -> AuthResponse:
    """Build a full AuthResponse for a given user."""
    access_token = create_access_token(user.id, user.role.name)
    refresh_token = create_refresh_token(user.id, user.role.name)
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        role=user.role.name,
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            provider=user.provider,
            profile_image=user.profile_image,
            is_verified=user.is_verified,
            role=user.role.name,
        ),
    )


# ==========================================================
# Register
# ==========================================================

@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = UserRepository.get_by_email(db, request.email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user_role = db.query(Role).filter(Role.name == "USER").first()

    if not user_role:
        logger.error("USER role not found in database during registration.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error. Please contact support.",
        )

    try:
        user = User(
            name=request.name,
            email=request.email,
            hashed_password=hash_password(request.password),
            provider="LOCAL",
            is_verified=False,
            is_active=True,
            role_id=user_role.id,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info("New user registered: %s", user.email)
    except Exception:
        db.rollback()
        logger.exception("Failed to create user during registration.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account. Please try again.",
        )

    # Send verification email if email service is configured
    if EmailService.is_configured():
        try:
            token = create_email_token(user.email)
            EmailService.send_verification_email(user.email, token)
        except Exception:
            # Non-fatal — user can request a new verification email
            logger.exception("Failed to send verification email to %s.", user.email)

    return _build_auth_response(user)


# ==========================================================
# Login
# ==========================================================

@router.post(
    "/login",
    response_model=AuthResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    user = UserRepository.get_by_email(db, request.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if user.provider == "GOOGLE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account uses Google Sign-In. Please use the Google login button.",
        )

    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password login is not available for this account.",
        )

    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been disabled. Please contact support.",
        )

    logger.info("User logged in: %s", user.email)
    return _build_auth_response(user)


# ==========================================================
# Google Login
# ==========================================================

@router.post(
    "/google-login",
    response_model=AuthResponse,
)
def google_login(
    request: GoogleLoginRequest,
    db: Session = Depends(get_db),
):
    try:
        user = GoogleAuthService.verify_google_token(request.credential, db)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Google login failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authentication failed. Please try again.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been disabled. Please contact support.",
        )

    logger.info("Google login: %s", user.email)
    return _build_auth_response(user)


# ==========================================================
# Get Current User
# ==========================================================

@router.get(
    "/me",
    response_model=UserResponse,
)
def current_user(
    current_user: User = Depends(get_current_user),
):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        provider=current_user.provider,
        profile_image=current_user.profile_image,
        is_verified=current_user.is_verified,
        role=current_user.role.name,
    )


# ==========================================================
# Refresh Token
# ==========================================================

@router.post("/refresh")
def refresh_token(request: RefreshTokenRequest):

    payload = verify_refresh_token(request.refresh_token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Prevent non-refresh tokens from being used here
    if not is_refresh_token(payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    access_token = create_access_token(
        payload["sub"],
        payload.get("role", "USER"),
    )

    return {"access_token": access_token, "token_type": "bearer"}


# ==========================================================
# Verify Email
# ==========================================================

@router.get("/verify-email")
def verify_email(
    token: str,
    db: Session = Depends(get_db),
):
    payload = verify_token(token)

    if not payload or not is_verify_token(payload):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification link.",
        )

    email = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed verification token.",
        )

    user = UserRepository.get_by_email(db, email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if user.is_verified:
        return {"message": "Email already verified."}

    UserRepository.verify_email(db, user)
    logger.info("Email verified for: %s", user.email)

    return {"message": "Email verified successfully."}


# ==========================================================
# Forgot Password
# ==========================================================

@router.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    # Always return the same message to prevent email enumeration
    user = UserRepository.get_by_email(db, request.email)

    if not user:
        return {
            "message": "If that email address is registered, you will receive a reset link shortly."
        }

    if user.provider == "GOOGLE":
        # Still return same message to prevent enumeration
        return {
            "message": "If that email address is registered, you will receive a reset link shortly."
        }

    try:
        # Invalidate all previous reset tokens for this user
        PasswordResetRepository.delete_all_for_email(db, user.email)

        token = create_password_reset_token(user.email)

        PasswordResetRepository.create(db=db, email=user.email, token=token)

        if EmailService.is_configured():
            EmailService.send_password_reset_email(user.email, token)
            logger.info("Password reset email sent to %s.", user.email)
        else:
            logger.warning(
                "Email service not configured — reset token created but not sent."
            )
    except Exception:
        db.rollback()
        logger.exception("Failed to process forgot-password for %s.", request.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process request. Please try again.",
        )

    return {
        "message": "If that email address is registered, you will receive a reset link shortly."
    }


# ==========================================================
# Reset Password
# ==========================================================

@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    # Validate JWT signature and expiry
    payload = verify_token(request.token)

    if not payload or not is_reset_token(payload):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    email = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed reset token.",
        )

    # Check token exists in DB (single-use enforcement)
    db_token = PasswordResetRepository.get_by_token(db, request.token)

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has already been used or does not exist.",
        )

    user = UserRepository.get_by_email(db, email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    try:
        # Update password and delete token in a single transaction
        user.hashed_password = hash_password(request.password)
        db.delete(db_token)
        db.commit()
        logger.info("Password reset successfully for %s.", user.email)
    except Exception:
        db.rollback()
        logger.exception("Failed to reset password for %s.", email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password. Please try again.",
        )

    return {"message": "Password updated successfully."}
