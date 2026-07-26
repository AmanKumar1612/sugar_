"""
init_roles.py — Seed the four system roles into the database.

Run once after first deployment (or after wiping the DB):
    cd backend
    PYTHONPATH=. python scripts/init_roles.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.role import Role

DEFAULT_ROLES = [
    {"id": "role-super-admin", "name": "SUPER_ADMIN"},
    {"id": "role-admin",       "name": "ADMIN"},
    {"id": "role-moderator",   "name": "MODERATOR"},
    {"id": "role-user",        "name": "USER"},
]


def main() -> None:
    db = SessionLocal()
    try:
        for item in DEFAULT_ROLES:
            exists = db.query(Role).filter(Role.name == item["name"]).first()
            if exists:
                print(f"  {item['name']} already exists — skipping.")
                continue
            db.add(Role(id=item["id"], name=item["name"]))
            print(f"  Created {item['name']}")
        db.commit()
        print("\nAll roles initialized successfully.")
    except Exception as exc:
        db.rollback()
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
