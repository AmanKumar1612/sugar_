import os
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session
from app.models.user import User

SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
ALGORITHM = 'HS256'


def create_access_token(subject: str, role: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=30)
    payload = {'sub': subject, 'role': role, 'exp': expires}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(subject: str, role: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    payload = {'sub': subject, 'role': role, 'exp': expires}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token') from exc


def get_token_from_request(request: Request):
    header = request.headers.get('Authorization', '')
    if header.startswith('Bearer '):
        return header.split(' ', 1)[1]
    return None


def get_current_user(db: Session, token: str):
    payload = decode_token(token)
    email = payload.get('sub')
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')
    return user
