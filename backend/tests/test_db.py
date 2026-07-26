"""
Quick connectivity check — uses DATABASE_URL from the environment.
Run from the backend/ directory:
    PYTHONPATH=. python tests/test_db.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine

try:
    with engine.connect() as conn:
        print("DATABASE CONNECTED SUCCESSFULLY")
except Exception as exc:
    print(f"Connection failed: {exc}")
    sys.exit(1)
