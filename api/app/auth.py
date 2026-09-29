from datetime import datetime,timedelta,timezone
from uuid import UUID
import hashlib
from jose import jwt
from pwdlib import PasswordHash
from fastapi import Depends,HTTPException,Header
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import settings
from .db import db
from .models import User,APIKey
pwd=PasswordHash.recommended()
def create_token(uid:UUID): return jwt.encode({"sub":str(uid),"exp":datetime.now(timezone.utc)+timedelta(hours=24)},settings.jwt_secret,algorithm="HS256")
def current_user(authorization:str=Header(default=""),session:Session=Depends(db)):
    if not authorization.startswith("Bearer "): raise HTTPException(401,"Authentication required")
    try: uid=UUID(jwt.decode(authorization[7:],settings.jwt_secret,algorithms=["HS256"])["sub"])
    except Exception: raise HTTPException(401,"Invalid or expired token")
    u=session.get(User,uid)
    if not u: raise HTTPException(401,"User not found")
    return u
def api_user(authorization:str=Header(default=""),session:Session=Depends(db)):
    if not authorization.startswith("Bearer "): raise HTTPException(401,"Authentication required")
    raw=authorization[7:]
    try:
        uid=UUID(jwt.decode(raw,settings.jwt_secret,algorithms=["HS256"])["sub"]); u=session.get(User,uid)
        if u:return u
    except Exception:pass
    k=session.scalar(select(APIKey).where(APIKey.key_hash==hashlib.sha256(raw.encode()).hexdigest(),APIKey.revoked==False))
    if not k:raise HTTPException(401,"Invalid API key or token")
    return session.get(User,k.user_id)
