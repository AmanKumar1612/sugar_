from sqlalchemy.orm import Session

from app.models.password_reset import PasswordResetToken


class PasswordResetRepository:

    @staticmethod
    def create(db: Session, email: str, token: str) -> PasswordResetToken:
        reset = PasswordResetToken(email=email, token=token)
        db.add(reset)
        db.commit()
        db.refresh(reset)
        return reset

    @staticmethod
    def get_by_token(db: Session, token: str) -> PasswordResetToken | None:
        return (
            db.query(PasswordResetToken)
            .filter(PasswordResetToken.token == token)
            .first()
        )

    @staticmethod
    def delete_all_for_email(db: Session, email: str) -> None:
        (
            db.query(PasswordResetToken)
            .filter(PasswordResetToken.email == email)
            .delete()
        )
        db.commit()
