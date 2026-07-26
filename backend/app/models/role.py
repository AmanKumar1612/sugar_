from sqlalchemy import (
    Column,
    String,
)

from sqlalchemy.orm import relationship

from app.core.database import Base


class Role(Base):

    __tablename__ = "roles"

    id = Column(
        String,
        primary_key=True
    )

    name = Column(
        String,
        unique=True,
        nullable=False
    )

    users = relationship(
        "User",
        back_populates="role"
    )