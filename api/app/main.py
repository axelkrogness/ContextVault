from fastapi import FastAPI,Depends,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,EmailStr,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
from .config import settings
from .db import Base,engine
from .models import User,Application,Agent,Memory
from .auth import db,current_user,create_token
Base.metadata.create_all(bind=engine)
app=FastAPI(title="ContextVault API",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
pwd=PasswordHash.recommended()
class Credentials(BaseModel):
 email:EmailStr
 password:str=Field(min_length=8)
class Name(BaseModel): name:str=Field(min_length=1,max_length=200)
class MemoryIn(BaseModel):
 agent_id:int
 content:str=Field(min_length=1)
 tags:list[str]=[]
 importance:float=Field(default=.5,ge=0,le=1)
@app.get("/")
def root(): return {"name":"ContextVault API","status":"ok","docs":"/docs"}
@app.get("/health")
def health(): return {"status":"ok"}
@app.post("/api/v1/auth/register")
def register(b:Credentials,s:Session=Depends(db)):
 if s.scalar(select(User).where(User.email==b.email)): raise HTTPException(409,"Email already registered")
 u=User(email=b.email,password_hash=pwd.hash(b.password));s.add(u);s.commit();s.refresh(u)
 return {"access_token":create_token(u.id),"token_type":"bearer"}
@app.post("/api/v1/auth/login")
def login(b:Credentials,s:Session=Depends(db)):
 u=s.scalar(select(User).where(User.email==b.email))
 if not u or not pwd.verify(b.password,u.password_hash): raise HTTPException(401,"Invalid email or password")
 return {"access_token":create_token(u.id),"token_type":"bearer"}
@app.get("/api/v1/auth/me")
def me(u:User=Depends(current_user)): return {"id":u.id,"email":u.email}
@app.post("/api/v1/applications")
def application(b:Name,u:User=Depends(current_user),s:Session=Depends(db)):
 x=Application(user_id=u.id,name=b.name);s.add(x);s.commit();s.refresh(x);return {"id":x.id,"name":x.name}
@app.post("/api/v1/agents")
def agent(b:dict,u:User=Depends(current_user),s:Session=Depends(db)):
 a=s.get(Application,int(b["application_id"]))
 if not a or a.user_id!=u.id: raise HTTPException(404,"Application not found")
 x=Agent(application_id=a.id,name=str(b["name"]),namespace=str(b.get("namespace","default")));s.add(x);s.commit();s.refresh(x);return {"id":x.id,"name":x.name}
@app.post("/api/v1/memories")
def memory(b:MemoryIn,u:User=Depends(current_user),s:Session=Depends(db)):
 a=s.get(Agent,b.agent_id);appx=s.get(Application,a.application_id) if a else None
 if not a or not appx or appx.user_id!=u.id: raise HTTPException(404,"Agent not found")
 x=Memory(agent_id=a.id,content=b.content,tags=",".join(b.tags),importance=b.importance);s.add(x);s.commit();s.refresh(x);return {"id":x.id,"content":x.content}
@app.get("/api/v1/memories")
def memories(u:User=Depends(current_user),s:Session=Depends(db)):
 rows=s.scalars(select(Memory).join(Agent,Memory.agent_id==Agent.id).join(Application,Agent.application_id==Application.id).where(Application.user_id==u.id).order_by(Memory.created_at.desc())).all()
 return [{"id":x.id,"content":x.content,"importance":x.importance} for x in rows]
@app.post("/api/v1/memories/search")
def search(b:dict,u:User=Depends(current_user),s:Session=Depends(db)):
 q=str(b.get("query","")).lower();rows=s.scalars(select(Memory).join(Agent,Memory.agent_id==Agent.id).join(Application,Agent.application_id==Application.id).where(Application.user_id==u.id)).all()
 return [{"id":x.id,"content":x.content,"importance":x.importance} for x in rows if q in x.content.lower()][:50]
