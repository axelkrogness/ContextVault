from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from uuid import UUID
class AuthIn(BaseModel): email:EmailStr; password:str=Field(min_length=8)
class Token(BaseModel): access_token:str; token_type:str='bearer'
class AppIn(BaseModel): name:str; slug:str
class AgentIn(BaseModel): application_id:UUID; name:str; namespace:str; description:str=''
class MemoryIn(BaseModel): agent_id:UUID; content:str; namespace:str; metadata:dict={}; tags:list[str]=[]; importance:float=Field(.5,ge=0,le=1); expires_at:datetime|None=None
class SearchIn(BaseModel): agent_id:UUID; query:str; namespace:str|None=None; tags:list[str]=[]; min_importance:float=0; include_archived:bool=False; limit:int=10
