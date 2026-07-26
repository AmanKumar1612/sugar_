"""
Import all models here so that SQLAlchemy's metadata knows about every table
before create_all() is called and Alembic can detect all models.
"""

from app.models.role import Role
from app.models.user import User
from app.models.chat import Chat
from app.models.chat_session import ChatSession
from app.models.message import Message
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.password_reset import PasswordResetToken
from app.models.search_log import SearchLog
from app.models.guest_session import GuestSession
from app.models.escalated_query import EscalatedQuery
