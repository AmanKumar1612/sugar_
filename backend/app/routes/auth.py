from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse
from app.services.password_service import hash_password, verify_password
from app.auth.jwt_utils import create_access_token, create_refresh_token, get_current_user

router = APIRouter()


@router.post('/signup', response_model=TokenResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail='Passwords do not match')

    existing = db.query(User).filter(User.email == str(payload.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail='Email already exists')

    if payload.role == 'admin' and payload.admin_secret_key != 'sugarcane-admin-2026':
        raise HTTPException(status_code=403, detail='Invalid admin secret key')

    user = User(
        full_name=payload.full_name,
        email=str(payload.email),
        password=hash_password(payload.password),
        phone=payload.phone,
        village=payload.village,
        district=payload.district,
        state=payload.state,
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(user.email, user.role)
    refresh_token = create_refresh_token(user.email, user.role)
    user.refresh_token = refresh_token
    db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token, role=user.role, email=user.email)


@router.post('/login', response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(payload.email)).first()
    if not user or not verify_password(payload.password, user.password or ''):
        raise HTTPException(status_code=401, detail='Invalid credentials')

    access_token = create_access_token(user.email, user.role)
    refresh_token = create_refresh_token(user.email, user.role)
    user.refresh_token = refresh_token
    db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token, role=user.role, email=user.email)


@router.post('/google', response_model=TokenResponse)
def google_login(payload: dict, db: Session = Depends(get_db)):
    email = payload.get('email')
    if not email:
        raise HTTPException(status_code=400, detail='Email is required')
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, full_name=payload.get('name', 'Google User'), role='farmer')
        db.add(user)
        db.commit()
        db.refresh(user)
    access_token = create_access_token(user.email, user.role)
    refresh_token = create_refresh_token(user.email, user.role)
    user.refresh_token = refresh_token
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, role=user.role, email=user.email)


@router.post('/refresh', response_model=TokenResponse)
def refresh(token: str, db: Session = Depends(get_db)):
    user = get_current_user(db, token)
    access_token = create_access_token(user.email, user.role)
    refresh_token = create_refresh_token(user.email, user.role)
    user.refresh_token = refresh_token
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, role=user.role, email=user.email)
