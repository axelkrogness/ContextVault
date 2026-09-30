import json,hashlib
from datetime import datetime,timedelta
from uuid import UUID
from jose import jwt
from fastapi import FastAPI,Depends,HTTPException,Header,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel,EmailStr,Field
from sqlalchemy import select,func,text,or_
from sqlalchemy.orm import Session
from .config import settings
from .db import Base,engine,db,SessionLocal
from .models import User,Application,Agent,Namespace,Memory,APIKey,APIUsage,Permission,RateLimitEvent
from .auth import pwd,current_user,api_user,create_token
from .services import embedding,cosine,new_api_key

with engine.begin() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    if not conn.execute(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='vector')")).scalar():
        raise RuntimeError("PostgreSQL pgvector extension is required but unavailable")
Base.metadata.create_all(bind=engine)
with engine.begin() as conn:
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cv_memories_created_at ON cv_memories (created_at DESC)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cv_memories_agent_archived ON cv_memories (agent_id, archived)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cv_usage_user_created ON cv_api_usage (user_id, created_at DESC)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cv_rate_user_created ON cv_rate_limit_events (user_id, created_at DESC)"))


app=FastAPI(title="ContextVault API",version="4.0.0")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

def token_user_id(request:Request):
    auth=request.headers.get("authorization","")
    if not auth.startswith("Bearer "): return None
    raw=auth[7:]
    try:return UUID(jwt.decode(raw,settings.jwt_secret,algorithms=["HS256"])["sub"])
    except Exception:
        try:
            with SessionLocal() as s:
                k=s.scalar(select(APIKey).where(APIKey.key_hash==hashlib.sha256(raw.encode()).hexdigest(),APIKey.revoked==False))
                return k.user_id if k else None
        except Exception:return None

@app.middleware("http")
async def audit_limit(request:Request,call_next):
    uid=token_user_id(request); status=500
    if uid:
        with SessionLocal() as s:
            cutoff=datetime.utcnow()-timedelta(minutes=1)
            cleanup=datetime.utcnow()-timedelta(days=1)
            s.query(RateLimitEvent).filter(RateLimitEvent.created_at<cleanup).delete(synchronize_session=False)
            s.commit()
            used=s.scalar(select(func.count()).select_from(RateLimitEvent).where(RateLimitEvent.user_id==uid,RateLimitEvent.created_at>=cutoff)) or 0
            if used>=settings.rate_limit_per_minute:
                return JSONResponse(status_code=429,content={"detail":"Rate limit exceeded"},headers={"Retry-After":"60"})
            s.add(RateLimitEvent(user_id=uid));s.commit()
    try:
        response=await call_next(request);status=response.status_code;return response
    finally:
        if uid:
            try:
                with SessionLocal() as s:
                    s.add(APIUsage(user_id=uid,endpoint=request.url.path,method=request.method,status_code=status));s.commit()
            except Exception:pass

class Credentials(BaseModel):email:EmailStr;password:str=Field(min_length=8)
class Name(BaseModel):name:str=Field(min_length=1,max_length=200)
class AgentIn(BaseModel):application_id:UUID;name:str=Field(min_length=1,max_length=200);namespace:str="default"
class NamespaceIn(BaseModel):agent_id:UUID;name:str=Field(min_length=1,max_length=200);retention_days:int|None=Field(default=None,ge=1)
class MemoryIn(BaseModel):
    agent_id:UUID;namespace_id:UUID|None=None;content:str=Field(min_length=1)
    tags:list[str]=Field(default_factory=list);metadata:dict=Field(default_factory=dict);importance:float=Field(default=.5,ge=0,le=1);expires_at:datetime|None=None
class MemoryUpdate(BaseModel):
    content:str|None=None;tags:list[str]|None=None;metadata:dict|None=None
    importance:float|None=Field(default=None,ge=0,le=1);expires_at:datetime|None=None
class SearchIn(BaseModel):
    query:str="";mode:str="hybrid";agent_id:UUID|None=None;namespace_id:UUID|None=None
    start_date:datetime|None=None;end_date:datetime|None=None;limit:int=Field(default=20,ge=1,le=100)
class EvalIn(SearchIn): relevant_ids:list[UUID]=Field(default_factory=list)
class KeyIn(BaseModel):name:str="default"

def permission(s,u,app_id,write=False):
    a=s.get(Application,app_id)
    if not a:raise HTTPException(404,"Application not found")
    if a.user_id==u.id:return "owner"
    owner=s.get(User,a.user_id)
    if owner and owner.privacy_mode:raise HTTPException(403,"Owner privacy mode blocks shared access")
    p=s.scalar(select(Permission).where(Permission.application_id==app_id,Permission.user_id==u.id))
    if not p:raise HTTPException(403,"No application permission")
    if write and p.role!="editor":raise HTTPException(403,"Editor permission required")
    return p.role

def agent_access(s,u,agent_id,write=False):
    a=s.get(Agent,agent_id)
    if not a:raise HTTPException(404,"Agent not found")
    permission(s,u,a.application_id,write);return a

def memory_access(s,u,mid,write=False):
    m=s.get(Memory,mid)
    if not m:raise HTTPException(404,"Memory not found")
    agent_access(s,u,m.agent_id,write);return m

def visible_app_ids(s,u):
    owned=list(s.scalars(select(Application.id).where(Application.user_id==u.id)).all())
    shared=[]
    for app_id in s.scalars(select(Permission.application_id).where(Permission.user_id==u.id)).all():
        a=s.get(Application,app_id);owner=s.get(User,a.user_id) if a else None
        if a and owner and not owner.privacy_mode:shared.append(app_id)
    return list(set(owned+shared))

def serialize_memory(x):
    return {"id":x.id,"agent_id":x.agent_id,"namespace_id":x.namespace_id,"content":x.content,
            "tags":x.tags.split(",") if x.tags else [],"metadata":json.loads(x.metadata_json or "{}"),
            "importance":x.importance,"archived":x.archived,"expires_at":x.expires_at,
            "created_at":x.created_at,"updated_at":x.updated_at}

def create_mem(b,u,s):
    agent_access(s,u,b.agent_id,True)
    if b.namespace_id:
        ns=s.get(Namespace,b.namespace_id)
        if not ns or ns.agent_id!=b.agent_id:raise HTTPException(400,"Namespace does not belong to agent")
    normalized=" ".join(b.content.lower().split())
    rows=s.scalars(select(Memory).where(Memory.agent_id==b.agent_id,Memory.archived==False)).all()
    exact=next((m for m in rows if " ".join(m.content.lower().split())==normalized),None)
    if exact:return exact,True
    v=embedding(b.content)
    dup=next((m for m in rows if cosine(v,list(m.embedding))>=.97),None)
    if dup:return dup,True
    effective_expiry=b.expires_at
    if not effective_expiry and b.namespace_id:
        ns=s.get(Namespace,b.namespace_id)
        if ns and ns.retention_days:effective_expiry=datetime.utcnow()+timedelta(days=ns.retention_days)
    x=Memory(agent_id=b.agent_id,namespace_id=b.namespace_id,content=b.content,tags=",".join(b.tags),
             metadata_json=json.dumps(b.metadata),embedding=v,importance=b.importance,expires_at=effective_expiry)
    s.add(x);s.commit();s.refresh(x);return x,False

@app.get("/")
def root():return {"name":"ContextVault API","status":"ok","docs":"/docs"}
@app.get("/health")
def health():return {"status":"ok","vector_storage":"pgvector","semantic_embeddings":"provider" if settings.embedding_api_url else "offline_fallback"}

@app.post("/api/v1/auth/register")
def register(b:Credentials,s:Session=Depends(db)):
    if s.scalar(select(User).where(User.email==b.email)):raise HTTPException(409,"Email already registered")
    u=User(email=b.email,password_hash=pwd.hash(b.password));s.add(u);s.commit();s.refresh(u)
    return {"access_token":create_token(u.id),"token_type":"bearer"}
@app.post("/api/v1/auth/login")
def login(b:Credentials,s:Session=Depends(db)):
    u=s.scalar(select(User).where(User.email==b.email))
    if not u or not pwd.verify(b.password,u.password_hash):raise HTTPException(401,"Invalid email or password")
    return {"access_token":create_token(u.id),"token_type":"bearer"}
@app.post("/api/v1/auth/logout")
def logout(u:User=Depends(current_user)):return {"status":"ok"}
@app.get("/api/v1/auth/me")
def me(u:User=Depends(current_user)):return {"id":u.id,"email":u.email,"privacy_mode":u.privacy_mode}

@app.post("/api/v1/applications")
def create_application(b:Name,u:User=Depends(current_user),s:Session=Depends(db)):
    x=Application(user_id=u.id,name=b.name);s.add(x);s.commit();s.refresh(x);return {"id":x.id,"name":x.name,"role":"owner"}
@app.get("/api/v1/applications")
def applications(u:User=Depends(current_user),s:Session=Depends(db)):
    ids=visible_app_ids(s,u);return [{"id":a.id,"name":a.name,"role":"owner" if a.user_id==u.id else s.scalar(select(Permission.role).where(Permission.application_id==a.id,Permission.user_id==u.id))} for a in s.scalars(select(Application).where(Application.id.in_(ids))).all()] if ids else []

@app.post("/api/v1/agents")
def create_agent(b:AgentIn,u:User=Depends(current_user),s:Session=Depends(db)):
    permission(s,u,b.application_id,True)
    x=Agent(application_id=b.application_id,name=b.name,namespace=b.namespace);s.add(x);s.commit();s.refresh(x);return {"id":x.id,"name":x.name}
@app.get("/api/v1/agents")
def agents(u:User=Depends(current_user),s:Session=Depends(db)):
    ids=visible_app_ids(s,u);rows=s.scalars(select(Agent).where(Agent.application_id.in_(ids))).all() if ids else []
    return [{"id":x.id,"name":x.name,"application_id":x.application_id} for x in rows]

@app.post("/api/v1/namespaces")
def create_namespace(b:NamespaceIn,u:User=Depends(current_user),s:Session=Depends(db)):
    agent_access(s,u,b.agent_id,True)
    x=Namespace(agent_id=b.agent_id,name=b.name,retention_days=b.retention_days);s.add(x);s.commit();s.refresh(x);return {"id":x.id,"name":x.name}
@app.get("/api/v1/namespaces")
def namespaces(u:User=Depends(current_user),s:Session=Depends(db)):
    ids=visible_app_ids(s,u)
    rows=s.scalars(select(Namespace).join(Agent).where(Agent.application_id.in_(ids))).all() if ids else []
    return [{"id":x.id,"agent_id":x.agent_id,"name":x.name,"retention_days":x.retention_days} for x in rows]

@app.post("/api/v1/memories")
def create_memory(b:MemoryIn,u:User=Depends(current_user),s:Session=Depends(db)):
    x,d=create_mem(b,u,s);return {"id":x.id,"content":x.content,"duplicate":d}
@app.post("/api/v1/memories/ingest")
def ingest(b:MemoryIn,u:User=Depends(api_user),s:Session=Depends(db)):
    x,d=create_mem(b,u,s);return {"id":x.id,"duplicate":d}
@app.get("/api/v1/memories")
def memories(u:User=Depends(current_user),s:Session=Depends(db)):
    ids=visible_app_ids(s,u);now=datetime.utcnow()
    rows=s.scalars(select(Memory).join(Agent).where(Agent.application_id.in_(ids)).order_by(Memory.created_at.desc())).all() if ids else []
    return [serialize_memory(x) for x in rows if not x.expires_at or x.expires_at>=now]
@app.put("/api/v1/memories/{mid}")
def update_memory(mid:UUID,b:MemoryUpdate,u:User=Depends(current_user),s:Session=Depends(db)):
    x=memory_access(s,u,mid,True)
    if b.content is not None:x.content=b.content;x.embedding=embedding(b.content)
    if b.tags is not None:x.tags=",".join(b.tags)
    if b.metadata is not None:x.metadata_json=json.dumps(b.metadata)
    if b.importance is not None:x.importance=b.importance
    if "expires_at" in b.model_fields_set:x.expires_at=b.expires_at
    s.commit();s.refresh(x);return serialize_memory(x)
@app.delete("/api/v1/memories/{mid}")
def delete_memory(mid:UUID,u:User=Depends(current_user),s:Session=Depends(db)):
    x=memory_access(s,u,mid,True);s.delete(x);s.commit();return {"status":"deleted"}
@app.post("/api/v1/memories/{mid}/archive")
def archive(mid:UUID,u:User=Depends(current_user),s:Session=Depends(db)):
    x=memory_access(s,u,mid,True);x.archived=True;s.commit();return {"status":"archived"}
@app.post("/api/v1/memories/{mid}/restore")
def restore(mid:UUID,u:User=Depends(current_user),s:Session=Depends(db)):
    x=memory_access(s,u,mid,True);x.archived=False;s.commit();return {"status":"restored"}
@app.get("/api/v1/memories/{mid}/similar")
def similar(mid:UUID,u:User=Depends(current_user),s:Session=Depends(db)):
    x=memory_access(s,u,mid);agent_access(s,u,x.agent_id);v=list(x.embedding)
    rows=s.scalars(select(Memory).where(Memory.agent_id==x.agent_id,Memory.id!=x.id,Memory.archived==False)).all()
    ranked=sorted(((cosine(v,list(m.embedding)),m) for m in rows),key=lambda z:z[0],reverse=True)[:10]
    return [{"id":m.id,"content":m.content,"similarity":round(sc,4)} for sc,m in ranked]

def run_search(b,u,s):
    ids=visible_app_ids(s,u);now=datetime.utcnow()
    q=select(Memory).join(Agent).where(Agent.application_id.in_(ids),Memory.archived==False) if ids else select(Memory).where(text("1=0"))
    if b.agent_id:agent_access(s,u,b.agent_id);q=q.where(Memory.agent_id==b.agent_id)
    if b.namespace_id:q=q.where(Memory.namespace_id==b.namespace_id)
    if b.start_date:q=q.where(Memory.created_at>=b.start_date)
    if b.end_date:q=q.where(Memory.created_at<=b.end_date)
    rows=s.scalars(q).all();txt=b.query.lower().strip();v=embedding(b.query) if txt else [];rank=[]
    for x in rows:
        if x.expires_at and x.expires_at<now:continue
        kw=1.0 if txt and txt in x.content.lower() else 0.0
        sem=cosine(v,list(x.embedding)) if txt else 0.0
        score=(kw+.05*x.importance) if b.mode=="keyword" else (sem+.05*x.importance) if b.mode=="semantic" else (.55*sem+.4*kw+.05*x.importance)
        rank.append((score,x))
    rank.sort(key=lambda z:z[0],reverse=True)
    return [{"id":x.id,"content":x.content,"score":round(float(sc),4),"importance":x.importance} for sc,x in rank[:b.limit]]

@app.post("/api/v1/memories/search")
def search(b:SearchIn,u:User=Depends(current_user),s:Session=Depends(db)):return run_search(b,u,s)
@app.post("/api/v1/retrieval-test")
def retrieval_test(b:SearchIn,u:User=Depends(current_user),s:Session=Depends(db)):
    r=run_search(b,u,s);return {"query":b.query,"mode":b.mode,"count":len(r),"results":r}
@app.post("/api/v1/evaluation")
def evaluation(b:EvalIn,u:User=Depends(current_user),s:Session=Depends(db)):
    r=run_search(b,u,s);retrieved=[UUID(str(x["id"])) for x in r]
    if b.relevant_ids:
        hits=len(set(retrieved)&set(b.relevant_ids))
        precision=hits/len(retrieved) if retrieved else 0;recall=hits/len(b.relevant_ids)
        return {"returned":len(r),"precision_at_k":round(precision,4),"recall_at_k":round(recall,4),"hits":hits}
    hits=sum(1 for x in r if b.query.lower() in x["content"].lower()) if b.query else 0
    return {"returned":len(r),"lexical_precision_proxy":round(hits/len(r),4) if r else 0,"note":"Provide relevant_ids for precision/recall evaluation."}
@app.post("/api/v1/context")
def context(b:SearchIn,u:User=Depends(current_user),s:Session=Depends(db)):
    r=run_search(b,u,s);return {"query":b.query,"context":"\n\n".join(x["content"] for x in r[:8]),"memories":r[:8]}

@app.post("/api/v1/api-keys")
def create_key(b:KeyIn,u:User=Depends(current_user),s:Session=Depends(db)):
    raw=new_api_key();x=APIKey(user_id=u.id,name=b.name,key_hash=hashlib.sha256(raw.encode()).hexdigest());s.add(x);s.commit();s.refresh(x);return {"id":x.id,"api_key":raw}
@app.get("/api/v1/api-keys")
def api_keys(u:User=Depends(current_user),s:Session=Depends(db)):
    return [{"id":x.id,"name":x.name,"revoked":x.revoked,"created_at":x.created_at} for x in s.scalars(select(APIKey).where(APIKey.user_id==u.id).order_by(APIKey.created_at.desc())).all()]
@app.post("/api/v1/api-keys/{kid}/revoke")
def revoke_key(kid:UUID,u:User=Depends(current_user),s:Session=Depends(db)):
    x=s.scalar(select(APIKey).where(APIKey.id==kid,APIKey.user_id==u.id))
    if not x:raise HTTPException(404,"API key not found")
    x.revoked=True;s.commit();return {"status":"revoked"}
@app.get("/api/v1/api-usage")
def usage(u:User=Depends(current_user),s:Session=Depends(db)):
    return [{"endpoint":x.endpoint,"method":x.method,"status_code":x.status_code,"created_at":x.created_at} for x in s.scalars(select(APIUsage).where(APIUsage.user_id==u.id).order_by(APIUsage.created_at.desc()).limit(250)).all()]
@app.get("/api/v1/rate-limit")
def rate_status(u:User=Depends(current_user),s:Session=Depends(db)):
    cutoff=datetime.utcnow()-timedelta(minutes=1)
    used=s.scalar(select(func.count()).select_from(RateLimitEvent).where(RateLimitEvent.user_id==u.id,RateLimitEvent.created_at>=cutoff)) or 0
    return {"limit":settings.rate_limit_per_minute,"used":used,"remaining":max(0,settings.rate_limit_per_minute-used)}

@app.post("/api/v1/privacy")
def privacy(enabled:bool,u:User=Depends(current_user),s:Session=Depends(db)):
    u.privacy_mode=enabled;s.commit();return {"privacy_mode":u.privacy_mode}
@app.post("/api/v1/permissions")
def add_permission(application_id:UUID,user_email:EmailStr,role:str="viewer",u:User=Depends(current_user),s:Session=Depends(db)):
    a=s.get(Application,application_id)
    if not a or a.user_id!=u.id:raise HTTPException(403,"Only owner can manage permissions")
    if role not in {"viewer","editor"}:raise HTTPException(400,"Role must be viewer or editor")
    target=s.scalar(select(User).where(User.email==user_email))
    if not target:raise HTTPException(404,"User not found")
    p=s.scalar(select(Permission).where(Permission.application_id==application_id,Permission.user_id==target.id))
    if p:p.role=role
    else:p=Permission(application_id=application_id,user_id=target.id,role=role);s.add(p)
    s.commit();s.refresh(p);return {"id":p.id,"role":p.role}
@app.get("/api/v1/permissions/{application_id}")
def permissions(application_id:UUID,u:User=Depends(current_user),s:Session=Depends(db)):
    a=s.get(Application,application_id)
    if not a or a.user_id!=u.id:raise HTTPException(403,"Only owner can view permissions")
    return [{"id":p.id,"user_id":p.user_id,"role":p.role} for p in s.scalars(select(Permission).where(Permission.application_id==application_id)).all()]

@app.post("/api/v1/retention/enforce")
def retention(u:User=Depends(current_user),s:Session=Depends(db)):
    ids=visible_app_ids(s,u);now=datetime.utcnow();archived=0
    rows=s.execute(select(Memory,Namespace,Agent).join(Namespace,Memory.namespace_id==Namespace.id).join(Agent,Memory.agent_id==Agent.id).where(Agent.application_id.in_(ids))).all() if ids else []
    for m,ns,a in rows:
        try:agent_access(s,u,a.id,True)
        except HTTPException:continue
        if (m.expires_at and m.expires_at<now) or (ns.retention_days and m.created_at<now-timedelta(days=ns.retention_days)):
            if not m.archived:m.archived=True;archived+=1
    s.commit();return {"archived":archived}

@app.get("/api/v1/export")
def export(u:User=Depends(current_user),s:Session=Depends(db)):return {"exported_at":datetime.utcnow(),"memories":memories(u,s)}
@app.get("/api/v1/analytics")
def analytics(u:User=Depends(current_user),s:Session=Depends(db)):
    data=memories(u,s)
    return {"memory_count":len(data),"storage_bytes":sum(len(x["content"].encode())+64*4 for x in data),
            "api_usage_count":s.scalar(select(func.count()).select_from(APIUsage).where(APIUsage.user_id==u.id)) or 0}

@app.get("/api/v1/system/readiness")
def readiness(u:User=Depends(current_user),s:Session=Depends(db)):
    vector_ok=bool(s.execute(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='vector')")).scalar())
    return {
        "database": "ok",
        "pgvector": vector_ok,
        "semantic_embeddings": "provider" if settings.embedding_api_url else "offline_fallback",
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "cors_configured": bool(settings.cors_origins),
        "ready": vector_ok
    }

