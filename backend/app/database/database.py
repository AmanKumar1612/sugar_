from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

DB_URL = os.getenv('DATABASE_URL', 'sqlite:///./sugarcane.db')
engine = create_engine(DB_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.models.user import User
    from app.models.knowledge import Knowledge
    from app.models.chat import Chat
    from app.models.document import Document

    Base.metadata.create_all(bind=engine)
