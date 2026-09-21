from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User
from ..schemas import AuthIn,Token
from ..security import hash_password,verify_password,token
r=APIRouter(prefix='/api/v1/auth',tags=['Auth'])
@r.post('/register',response_model=Token)
def register(x:AuthIn,db:Session=Depends(get_db)):
    if db.query(User).filter_by(email=x.email).first(): raise HTTPException(409,'Email already registered')
    u=User(email=x.email,password_hash=hash_password(x.password)); db.add(u); db.commit(); db.refresh(u); return Token(access_token=token(u.id))
@r.post('/login',response_model=Token)
def login(x:AuthIn,db:Session=Depends(get_db)):
    u=db.query(User).filter_by(email=x.email).first()
    if not u or not verify_password(x.password,u.password_hash): raise HTTPException(401,'Invalid credentials')
    return Token(access_token=token(u.id))
