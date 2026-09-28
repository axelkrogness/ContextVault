from datetime import datetime,timedelta,timezone
from jose import jwt
from passlib.context import CryptContext
from fastapi import Depends,HTTPException,Header
from sqlalchemy.orm import Session
from .config import settings
from .db import SessionLocal
from .models import User
pwd=CryptContext(schemes=["bcrypt"],deprecated="auto")
def db():
 s=SessionLocal()
 try: yield s
 finally: s.close()
def create_token(uid:int):
 return jwt.encode({"sub":str(uid),"exp":datetime.now(timezone.utc)+timedelta(hours=24)},settings.jwt_secret,algorithm="HS256")
def current_user(authorization:str=Header(default=""),session:Session=Depends(db)):
 if not authorization.startswith("Bearer "): raise HTTPException(401,"Authentication required")
 try: uid=int(jwt.decode(authorization[7:],settings.jwt_secret,algorithms=["HS256"])["sub"])
 except Exception: raise HTTPException(401,"Invalid or expired token")
 u=session.get(User,uid)
 if not u: raise HTTPException(401,"User not found")
 return u
