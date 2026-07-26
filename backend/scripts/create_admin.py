import os
import sys
from getpass import getpass

# Make sure the project root (backend/) is on sys.path regardless of cwd/OS,
# so `python scripts/create_admin.py` works the same as `python -m scripts.create_admin`.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import SessionLocal

from app.models.user import User
from app.models.role import Role

from app.core.security import hash_password


db = SessionLocal()

try:

    admin_role = (

        db.query(Role)

        .filter(Role.name == "SUPER_ADMIN")

        .first()

    )

    if admin_role is None:

        print("Run init_roles.py first.")

        exit()

    email = input("Email : ")

    existing = (

        db.query(User)

        .filter(User.email == email)

        .first()

    )

    if existing:

        print("Admin already exists.")

        exit()

    name = input("Name : ")

    password = getpass("Password : ")

    admin = User(

        name=name,

        email=email,

        hashed_password=hash_password(password),

        role_id=admin_role.id,

        is_verified=True,

        is_active=True,

    )

    db.add(admin)

    db.commit()

    print("\nSUPER ADMIN CREATED SUCCESSFULLY")

finally:

    db.close()