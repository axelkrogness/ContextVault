from datetime import datetime
from uuid import UUID,uuid4
from sqlalchemy import String,Text,DateTime,ForeignKey,Float,Boolean,Integer,Uuid,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column
from pgvector.sqlalchemy import Vector
from .db import Base
class User(Base):
    __tablename__="cv_users"; id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4); email:Mapped[str]=mapped_column(String(320),unique=True,index=True); password_hash:Mapped[str]=mapped_column(String(255)); privacy_mode:Mapped[bool]=mapped_column(Boolean,default=True); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class Application(Base):
    __tablename__="cv_applications"; id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4); user_id:Mapped[UUID]=mapped_column(Uuid,ForeignKey("cv_users.id"),index=True); name:Mapped[str]=mapped_column(String(200)); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class Agent(Base):
    __tablename__="cv_agents"; id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4); application_id:Mapped[UUID]=mapped_column(Uuid,ForeignKey("cv_applications.id"),index=True); name:Mapped[str]=mapped_column(String(200)); namespace:Mapped[str]=mapped_column(String(200),default="default"); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class Namespace(Base):
    __tablename__="cv_namespaces"; id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4); agent_id:Mapped[UUID]=mapped_column(Uuid,ForeignKey("cv_agents.id"),index=True); name:Mapped[str]=mapped_column(String(200)); retention_days:Mapped[int|None]=mapped_column(Integer,nullable=True); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); __table_args__=(UniqueConstraint("agent_id","name",name="uq_cv_ns"),)
class Memory(Base):
    __tablename__="cv_memories"; id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4); agent_id:Mapped[UUID]=mapped_column(Uuid,ForeignKey("cv_agents.id"),index=True); namespace_id:Mapped[UUID|None]=mapped_column(Uuid,ForeignKey("cv_namespaces.id"),nullable=True,index=True); content:Mapped[str]=mapped_column(Text); tags:Mapped[str]=mapped_column(Text,default=""); metadata_json:Mapped[str]=mapped_column(Text,default="{}"); embedding:Mapped[list[float]]=mapped_column(Vector(64)); importance:Mapped[float]=mapped_column(Float,default=.5); archived:Mapped[bool]=mapped_column(Boolean,default=False); expires_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); updated_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)
class APIKey(Base):
    __tablename__="cv_api_keys"; id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4); user_id:Mapped[UUID]=mapped_column(Uuid,ForeignKey("cv_users.id"),index=True); name:Mapped[str]=mapped_column(String(200)); key_hash:Mapped[str]=mapped_column(String(128),unique=True,index=True); revoked:Mapped[bool]=mapped_column(Boolean,default=False); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class APIUsage(Base):
    __tablename__="cv_api_usage"; id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4); user_id:Mapped[UUID]=mapped_column(Uuid,ForeignKey("cv_users.id"),index=True); endpoint:Mapped[str]=mapped_column(String(300)); method:Mapped[str]=mapped_column(String(20)); status_code:Mapped[int]=mapped_column(Integer); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class Permission(Base):
    __tablename__="cv_permissions"
    id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4)
    application_id:Mapped[UUID]=mapped_column(Uuid,ForeignKey("cv_applications.id"),index=True)
    user_id:Mapped[UUID]=mapped_column(Uuid,ForeignKey("cv_users.id"),index=True)
    role:Mapped[str]=mapped_column(String(30),default="viewer")
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    __table_args__=(UniqueConstraint("application_id","user_id",name="uq_cv_permission_user_app"),)

class RateLimitEvent(Base):
    __tablename__="cv_rate_limit_events"
    id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4)
    user_id:Mapped[UUID]=mapped_column(Uuid,ForeignKey("cv_users.id"),index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)
