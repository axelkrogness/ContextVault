import uuid,secrets,hashlib,time
from fastapi import APIRouter,Depends,HTTPException,Header
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User,Application,Agent,Memory,ApiKey,UsageLog
from ..schemas import AppIn,AgentIn,MemoryIn,SearchIn
from ..security import current_user
from ..services.embedding import EmbeddingService
r=APIRouter(prefix='/api/v1',tags=['ContextVault']); emb=EmbeddingService()
def app_owned(db,user,app_id):
    a=db.get(Application,app_id)
    if not a or a.user_id!=user.id: raise HTTPException(404,'Application not found')
    return a
def agent_owned(db,user,agent_id):
    g=db.get(Agent,agent_id)
    if not g: raise HTTPException(404,'Agent not found')
    app_owned(db,user,g.application_id); return g
@r.get('/me')
def me(user:User=Depends(current_user)): return {'id':str(user.id),'email':user.email}
@r.post('/applications')
def create_app(x:AppIn,db:Session=Depends(get_db),user=Depends(current_user)):
    a=Application(user_id=user.id,name=x.name,slug=x.slug); db.add(a); db.commit(); db.refresh(a); return {'id':str(a.id),'name':a.name,'slug':a.slug}
@r.get('/applications')
def apps(db:Session=Depends(get_db),user=Depends(current_user)):
    return [{'id':str(a.id),'name':a.name,'slug':a.slug} for a in db.query(Application).filter_by(user_id=user.id).all()]
@r.post('/agents')
def create_agent(x:AgentIn,db=Depends(get_db),user=Depends(current_user)):
    app_owned(db,user,x.application_id); g=Agent(application_id=x.application_id,name=x.name,namespace=x.namespace,description=x.description); db.add(g); db.commit(); db.refresh(g); return {'id':str(g.id),'name':g.name,'namespace':g.namespace}
@r.get('/agents')
def agents(db=Depends(get_db),user=Depends(current_user)):
    ids=[a.id for a in db.query(Application).filter_by(user_id=user.id).all()]; return [{'id':str(g.id),'name':g.name,'namespace':g.namespace} for g in db.query(Agent).filter(Agent.application_id.in_(ids)).all()] if ids else []
@r.post('/memories')
def create_memory(x:MemoryIn,db=Depends(get_db),user=Depends(current_user),x_api_key:str|None=Header(default=None)):
    g=agent_owned(db,user,x.agent_id); e=emb.embed(x.content)
    dup=db.query(Memory).filter(Memory.agent_id==g.id,Memory.content==x.content,Memory.archived==False).first()
    if dup: return {'id':str(dup.id),'duplicate':True,'message':'Existing identical memory returned'}
    m=Memory(agent_id=g.id,content=x.content,namespace=x.namespace,metadata_json=x.metadata,tags=x.tags,importance=x.importance,expires_at=x.expires_at,embedding=e); db.add(m); db.commit(); db.refresh(m); return {'id':str(m.id),'duplicate':False}
@r.post('/memories/search')
def search(x:SearchIn,db=Depends(get_db),user=Depends(current_user)):
    g=agent_owned(db,user,x.agent_id); q=emb.embed(x.query); query=db.query(Memory).filter(Memory.agent_id==g.id,Memory.importance>=x.min_importance)
    if x.namespace: query=query.filter(Memory.namespace==x.namespace)
    if not x.include_archived: query=query.filter(Memory.archived==False)
    rows=query.all()
    def score(m):
        sim=sum(a*b for a,b in zip(q,m.embedding or [])); kw=sum(t.lower() in m.content.lower() for t in x.query.split()); tag=sum(t in (m.tags or []) for t in x.tags); return sim*0.65+min(kw,5)*.07+tag*.08+m.importance*.2
    out=sorted(rows,key=score,reverse=True)[:x.limit]
    return {'results':[{'id':str(m.id),'content':m.content,'namespace':m.namespace,'tags':m.tags,'metadata':m.metadata_json,'importance':m.importance,'score':round(score(m),4),'created_at':m.created_at.isoformat()} for m in out]}
@r.post('/memories/retrieve')
def retrieve(x:SearchIn,db=Depends(get_db),user=Depends(current_user)):
    return search(x,db,user)
@r.post('/memories/similar')
def similar(x:SearchIn,db=Depends(get_db),user=Depends(current_user)):
    g=agent_owned(db,user,x.agent_id); q=emb.embed(x.query)
    rows=db.query(Memory).filter(Memory.agent_id==g.id,Memory.archived==False).all()
    ranked=sorted(rows,key=lambda m:sum(a*b for a,b in zip(q,m.embedding or [])),reverse=True)[:x.limit]
    return {'suggestions':[{'id':str(m.id),'content':m.content,'similarity':round(sum(a*b for a,b in zip(q,m.embedding or [])),4)} for m in ranked]}
@r.post('/evaluation/search-quality')
def search_quality(x:SearchIn,db=Depends(get_db),user=Depends(current_user)):
    result=search(x,db,user)['results']
    # Lightweight operational evaluation: reports result count and score statistics.
    scores=[r['score'] for r in result]
    return {'query':x.query,'result_count':len(result),'mean_score':round(sum(scores)/len(scores),4) if scores else 0,'top_score':max(scores) if scores else 0}
@r.post('/memories/{memory_id}/archive')
def archive(memory_id:uuid.UUID,db=Depends(get_db),user=Depends(current_user)):
    m=db.get(Memory,memory_id); 
    if not m: raise HTTPException(404,'Memory not found')
    agent_owned(db,user,m.agent_id); m.archived=True; db.commit(); return {'ok':True}
@r.post('/memories/{memory_id}/restore')
def restore(memory_id:uuid.UUID,db=Depends(get_db),user=Depends(current_user)):
    m=db.get(Memory,memory_id); 
    if not m: raise HTTPException(404,'Memory not found')
    agent_owned(db,user,m.agent_id); m.archived=False; db.commit(); return {'ok':True}
@r.delete('/memories/{memory_id}')
def delete(memory_id:uuid.UUID,db=Depends(get_db),user=Depends(current_user)):
    m=db.get(Memory,memory_id); 
    if not m: raise HTTPException(404,'Memory not found')
    agent_owned(db,user,m.agent_id); db.delete(m); db.commit(); return {'ok':True}
@r.post('/api-keys')
def create_key(application_id:uuid.UUID,name:str='Production',db=Depends(get_db),user=Depends(current_user)):
    app_owned(db,user,application_id); raw='cv_'+secrets.token_urlsafe(32); k=ApiKey(application_id=application_id,name=name,key_hash=hashlib.sha256(raw.encode()).hexdigest(),prefix=raw[:10]); db.add(k); db.commit(); return {'id':str(k.id),'key':raw,'warning':'Store this secret now; it is not shown again.'}
@r.get('/usage')
def usage(db=Depends(get_db),user=Depends(current_user)):
    apps=db.query(Application).filter_by(user_id=user.id).all(); ids=[a.id for a in apps]
    count=db.query(func.count(UsageLog.id)).filter(UsageLog.application_id.in_(ids)).scalar() if ids else 0
    memories=db.query(func.count(Memory.id)).join(Agent).join(Application).filter(Application.user_id==user.id).scalar()
    return {'api_requests':count,'memories':memories,'storage_estimate_kb':round(memories*1.8,1)}
@r.get('/export')
def export(db=Depends(get_db),user=Depends(current_user)):
    rows=db.query(Memory).join(Agent).join(Application).filter(Application.user_id==user.id).all()
    return {'memories':[{'id':str(m.id),'agent_id':str(m.agent_id),'content':m.content,'namespace':m.namespace,'tags':m.tags,'metadata':m.metadata_json,'importance':m.importance,'archived':m.archived} for m in rows]}
