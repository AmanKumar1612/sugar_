"""
make_admin.py
-------------
Promote an existing user to ADMIN role.

Usage:
    ADMIN_EMAIL=user@example.com python admin/make_admin.py

Or with explicit PYTHONPATH from the backend directory:
    PYTHONPATH=. ADMIN_EMAIL=user@example.com python admin/make_admin.py
"""

import os
import sys

# Allow running from the backend/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.role import Role


def main() -> None:
    email = os.environ.get("ADMIN_EMAIL", "").strip()

    if not email:
        print("ERROR: Set the ADMIN_EMAIL environment variable.", file=sys.stderr)
        sys.exit(1)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()

        if not user:
            print(f"ERROR: No user found with email '{email}'.", file=sys.stderr)
            sys.exit(1)

        admin_role = db.query(Role).filter(Role.name == "ADMIN").first()

        if not admin_role:
            print(
                "ERROR: ADMIN role not found in the database. "
                "Run the role seeder first.",
                file=sys.stderr,
            )
            sys.exit(1)

        if user.role_id == admin_role.id:
            print(f"User '{email}' is already an ADMIN.")
            return

        user.role_id = admin_role.id
        db.commit()
        print(f"Successfully promoted '{email}' to ADMIN.")

    except Exception as exc:
        db.rollback()
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
