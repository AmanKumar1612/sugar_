from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.database.database import init_db
from app.routes.auth import router as auth_router
from app.routes.chat import router as chat_router
from app.routes.knowledge import router as knowledge_router
from app.routes.users import router as users_router
from app.rag.knowledge_base import rag

load_dotenv()

app = FastAPI(title='Sugarcane AI – Smart Farmer Assistant', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:5173',
        'http://localhost:5174',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:5174',
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth_router, prefix='/auth', tags=['auth'])
app.include_router(chat_router, prefix='', tags=['chat'])
app.include_router(knowledge_router, prefix='/knowledge', tags=['knowledge'])
app.include_router(users_router, prefix='/users', tags=['users'])

@app.on_event('startup')
def startup_event():
    init_db()
    rag.seed_knowledge()

@app.get('/')
def health():
    return {'message': 'Sugarcane AI API is running'}
