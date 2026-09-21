from datetime import datetime,timedelta,timezone
from jose import jwt,JWTError
from passlib.context import CryptContext
from fastapi import Depends,HTTPException,status
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import User
pwd=CryptContext(schemes=['bcrypt'],deprecated='auto'); bearer=HTTPBearer()
def hash_password(p): return pwd.hash(p)
def verify_password(p,h): return pwd.verify(p,h)
def token(user_id): return jwt.encode({'sub':str(user_id),'exp':datetime.now(timezone.utc)+timedelta(hours=24)},settings.jwt_secret,algorithm='HS256')
def current_user(c:HTTPAuthorizationCredentials=Depends(bearer),db:Session=Depends(get_db)):
    try: uid=jwt.decode(c.credentials,settings.jwt_secret,algorithms=['HS256'])['sub']
    except (JWTError,KeyError): raise HTTPException(status_code=401,detail='Invalid or expired token')
    u=db.get(User,uid)
    if not u: raise HTTPException(status_code=401,detail='User not found')
    return u
