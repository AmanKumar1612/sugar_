from app.core.database import SessionLocal
from app.models.user import User

db = SessionLocal()

users = db.query(User).all()

for user in users:

    role_name = (
        user.role.name
        if user.role
        else "NO ROLE"
    )

    print(
        user.email,
        role_name
    )