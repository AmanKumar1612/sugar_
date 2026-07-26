import logging

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:

    BASE_URL = "https://api.resend.com/emails"

    @classmethod
    def is_configured(cls) -> bool:
        """Return True only if the email service has valid credentials."""
        return bool(settings.RESEND_API_KEY and settings.EMAIL_FROM)

    @classmethod
    def send_email(
        cls,
        to: str,
        subject: str,
        html: str,
    ) -> dict:
        if not cls.is_configured():
            logger.warning(
                "Email service is not configured — skipping send to %s ('%s').",
                to,
                subject,
            )
            return {}

        headers = {
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "from": settings.EMAIL_FROM,
            "to": [to],
            "subject": subject,
            "html": html,
        }

        response = requests.post(
            cls.BASE_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    @classmethod
    def send_verification_email(cls, email: str, token: str) -> dict:
        verify_link = (
            f"{settings.FRONTEND_URL.rstrip('/')}/verify-email?token={token}"
        )

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:24px;">
            <h2 style="color:#1a1a1a;">Welcome to the Sugarcane Dept Chatbot</h2>
            <p>Thank you for creating your account. Please verify your email address to get started.</p>
            <p>
                <a href="{verify_link}"
                   style="display:inline-block;background:#000;color:#fff;
                          padding:12px 24px;text-decoration:none;border-radius:6px;">
                    Verify Email
                </a>
            </p>
            <p style="color:#666;font-size:13px;">This link expires in 24 hours.</p>
            <p style="color:#666;font-size:13px;">
                If you didn't create an account, you can safely ignore this email.
            </p>
        </div>
        """

        return cls.send_email(
            to=email,
            subject="Verify your Sugarcane Dept Chatbot admin account",
            html=html,
        )

    @classmethod
    def send_password_reset_email(cls, email: str, token: str) -> dict:
        reset_link = (
            f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={token}"
        )

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:24px;">
            <h2 style="color:#1a1a1a;">Reset Your Password</h2>
            <p>We received a request to reset the password for your Sugarcane Dept Chatbot admin account.</p>
            <p>
                <a href="{reset_link}"
                   style="display:inline-block;background:#000;color:#fff;
                          padding:12px 24px;text-decoration:none;border-radius:6px;">
                    Reset Password
                </a>
            </p>
            <p style="color:#666;font-size:13px;">This link expires in 30 minutes.</p>
            <p style="color:#666;font-size:13px;">
                If you didn't request a password reset, you can safely ignore this email.
            </p>
        </div>
        """

        return cls.send_email(
            to=email,
            subject="Reset your Sugarcane Dept Chatbot password",
            html=html,
        )
