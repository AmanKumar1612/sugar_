from app.core.database import SessionLocal

from app.models.user import User
from app.models.role import Role


db = SessionLocal()

try:

    email = input("User Email : ")

    user = (

        db.query(User)

        .filter(User.email == email)

        .first()

    )

    if user is None:

        print("User not found.")

        exit()

    role = (

        db.query(Role)

        .filter(Role.name == "ADMIN")

        .first()

    )

    if role is None:

        print("Run init_roles.py")

        exit()

    user.role_id = role.id

    db.commit()

    print("User promoted to ADMIN.")

finally:

    db.close()