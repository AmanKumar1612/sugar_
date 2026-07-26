import logging

from fastapi import HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.role import Role

logger = logging.getLogger(__name__)


class GoogleAuthService:

    @staticmethod
    def verify_google_token(credential: str, db: Session) -> User:
        """
        Verify the Google ID token, then return the matching User
        (creating one if this is their first login).

        Raises HTTPException on any failure.
        """
        try:
            idinfo = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except Exception as exc:
            logger.warning("Google token verification failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token. Please try signing in again.",
            )

        email: str | None = idinfo.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account has no associated email address.",
            )

        email_verified: bool = idinfo.get("email_verified", False)
        if not email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account email is not verified.",
            )

        # Return existing user if already registered
        user = db.query(User).filter(User.email == email).first()
        if user:
            logger.debug("Google login: returning existing user %s", email)
            return user

        # First-time Google sign-in — create account
        role = db.query(Role).filter(Role.name == "USER").first()
        if not role:
            logger.error("USER role not found during Google sign-in for %s", email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server configuration error. Please contact support.",
            )

        try:
            user = User(
                name=idinfo.get("name") or email.split("@")[0],
                email=email,
                hashed_password=None,
                provider="GOOGLE",
                is_verified=True,
                is_active=True,
                profile_image=idinfo.get("picture"),
                role_id=role.id,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("New user created via Google sign-in: %s", email)
        except Exception:
            db.rollback()
            logger.exception("Failed to create user via Google sign-in for %s", email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create account. Please try again.",
            )

        return user
