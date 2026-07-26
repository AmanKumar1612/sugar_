from app.core.database import SessionLocal
from app.models.role import Role

db = SessionLocal()

roles = db.query(Role).all()

for role in roles:
    print(
        role.id,
        role.name
    )