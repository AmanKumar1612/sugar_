from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.chat import Chat
from app.auth.jwt_utils import get_current_user, get_token_from_request
from app.rag.knowledge_base import rag

router = APIRouter()


@router.post('/chat')
def chat(payload: dict, request: Request, db: Session = Depends(get_db)):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token missing')
    user = get_current_user(db, token)
    question = payload.get('question', '')
    if not question:
        raise HTTPException(status_code=400, detail='Question is required')
    response = rag.answer(question)
    chat_entry = Chat(user_id=user.id, question=question, answer=response['answer'])
    db.add(chat_entry)
    db.commit()
    return {'answer': response['answer'], 'sources': response['sources']}


@router.get('/history')
def history(request: Request, db: Session = Depends(get_db)):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token missing')
    user = get_current_user(db, token)
    chats = db.query(Chat).filter(Chat.user_id == user.id).order_by(Chat.timestamp.desc()).all()
    return [{'id': c.id, 'question': c.question, 'answer': c.answer, 'timestamp': str(c.timestamp)} for c in chats]


@router.delete('/history')
def clear_history(request: Request, db: Session = Depends(get_db)):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token missing')
    user = get_current_user(db, token)
    db.query(Chat).filter(Chat.user_id == user.id).delete()
    db.commit()
    return {'message': 'History cleared'}
