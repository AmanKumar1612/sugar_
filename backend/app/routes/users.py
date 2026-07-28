from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.user import User
from app.auth.jwt_utils import get_current_user, get_token_from_request

router = APIRouter()


@router.get('')
def list_users(request: Request, db: Session = Depends(get_db)):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token missing')
    user = get_current_user(db, token)
    if user.role != 'admin':
        raise HTTPException(status_code=403, detail='Admin only')
    users = db.query(User).all()
    return [{'id': u.id, 'full_name': u.full_name, 'email': u.email, 'role': u.role} for u in users]


@router.delete('/{user_id}')
def delete_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token missing')
    user = get_current_user(db, token)
    if user.role != 'admin':
        raise HTTPException(status_code=403, detail='Admin only')
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail='User not found')
    db.delete(target)
    db.commit()
    return {'message': 'User deleted'}
