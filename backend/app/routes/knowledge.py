from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.knowledge import Knowledge
from app.models.document import Document
from app.schemas.knowledge import KnowledgeCreate, KnowledgeUpdate
from app.auth.jwt_utils import get_current_user, get_token_from_request
from app.rag.knowledge_base import rag

router = APIRouter()


@router.get('')
def list_knowledge(db: Session = Depends(get_db)):
    items = db.query(Knowledge).order_by(Knowledge.created_at.desc()).all()
    return [{'id': item.id, 'title': item.title, 'category': item.category, 'question': item.question, 'answer': item.answer, 'keywords': item.keywords, 'created_at': str(item.created_at)} for item in items]


@router.post('', status_code=201)
def create_knowledge(payload: KnowledgeCreate, request: Request, db: Session = Depends(get_db)):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token missing')
    user = get_current_user(db, token)
    if user.role != 'admin':
        raise HTTPException(status_code=403, detail='Admin only')
    item = Knowledge(**payload.dict())
    db.add(item)
    db.commit()
    db.refresh(item)
    rag.add_document(item)
    return {'message': 'Knowledge created'}


@router.put('/{knowledge_id}')
def update_knowledge(knowledge_id: int, payload: KnowledgeUpdate, request: Request, db: Session = Depends(get_db)):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token missing')
    user = get_current_user(db, token)
    if user.role != 'admin':
        raise HTTPException(status_code=403, detail='Admin only')
    item = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
    if not item:
        raise HTTPException(status_code=404, detail='Knowledge not found')
    for key, value in payload.dict().items():
        setattr(item, key, value)
    db.commit()
    rag.add_document(item)
    return {'message': 'Knowledge updated'}


@router.delete('/{knowledge_id}')
def delete_knowledge(knowledge_id: int, request: Request, db: Session = Depends(get_db)):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token missing')
    user = get_current_user(db, token)
    if user.role != 'admin':
        raise HTTPException(status_code=403, detail='Admin only')
    item = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
    if not item:
        raise HTTPException(status_code=404, detail='Knowledge not found')
    db.delete(item)
    db.commit()
    return {'message': 'Knowledge deleted'}


@router.post('/upload')
def upload_document(request: Request, db: Session = Depends(get_db)):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token missing')
    user = get_current_user(db, token)
    if user.role != 'admin':
        raise HTTPException(status_code=403, detail='Admin only')
    document = Document(filename='sample.txt', path='uploads/sample.txt', uploaded_by=user.id)
    db.add(document)
    db.commit()
    return {'message': 'Document uploaded'}
