from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .db import Base,engine
from .routers import auth,core
app=FastAPI(title='ContextVault API',version='1.0.0',description='Long-term memory infrastructure for AI agents with hybrid RAG retrieval.')
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(',')],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
@app.on_event('startup')
def startup(): Base.metadata.create_all(engine)
@app.get('/health')
def health(): return {'status':'ok','service':'contextvault-api'}
app.include_router(auth.r); app.include_router(core.r)
