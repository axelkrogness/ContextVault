import hashlib, math, re
import httpx
from .config import settings
DIM=64

def _fallback_embedding(text:str)->list[float]:
    v=[0.0]*DIM
    for token in re.findall(r"[a-z0-9]+",text.lower()):
        h=hashlib.sha256(token.encode()).digest()
        for i in range(DIM): v[i]+=((h[i%32]/255.0)*2-1)
    n=math.sqrt(sum(x*x for x in v)) or 1
    return [x/n for x in v]

def embedding(text:str)->list[float]:
    if settings.embedding_api_url:
        headers={"Content-Type":"application/json"}
        if settings.embedding_api_key: headers["Authorization"]=f"Bearer {settings.embedding_api_key}"
        try:
            r=httpx.post(settings.embedding_api_url,headers=headers,json={"input":text,"dimensions":DIM},timeout=15)
            r.raise_for_status();data=r.json()
            raw=data.get("embedding") or (data.get("data") or [{}])[0].get("embedding")
            if raw and len(raw)>=DIM:
                raw=[float(x) for x in raw[:DIM]]
                n=math.sqrt(sum(x*x for x in raw)) or 1
                return [x/n for x in raw]
        except Exception: pass
    return _fallback_embedding(text)

def cosine(a,b):
    if not a or not b:return 0.0
    return sum(x*y for x,y in zip(a,b))/((math.sqrt(sum(x*x for x in a))*math.sqrt(sum(y*y for y in b))) or 1)

def new_api_key():
    import secrets
    return "cv_"+secrets.token_urlsafe(32)
