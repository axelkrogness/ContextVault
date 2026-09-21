import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, Float, Integer, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from .db import Base
class User(Base):
    __tablename__='users'; id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4); email:Mapped[str]=mapped_column(String(320),unique=True,index=True); password_hash:Mapped[str]=mapped_column(String(255)); created_at:Mapped[datetime]=mapped_column(DateTime,server_default=func.now())
class Application(Base):
    __tablename__='applications'; id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4); user_id:Mapped[uuid.UUID]=mapped_column(ForeignKey('users.id',ondelete='CASCADE'),index=True); name:Mapped[str]=mapped_column(String(160)); slug:Mapped[str]=mapped_column(String(160),index=True); privacy:Mapped[dict]=mapped_column(JSON,default=dict); created_at:Mapped[datetime]=mapped_column(DateTime,server_default=func.now())
class Agent(Base):
    __tablename__='agents'; id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4); application_id:Mapped[uuid.UUID]=mapped_column(ForeignKey('applications.id',ondelete='CASCADE'),index=True); name:Mapped[str]=mapped_column(String(160)); namespace:Mapped[str]=mapped_column(String(160),index=True); description:Mapped[str]=mapped_column(Text,default=''); created_at:Mapped[datetime]=mapped_column(DateTime,server_default=func.now())
class Memory(Base):
    __tablename__='memories'; id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4); agent_id:Mapped[uuid.UUID]=mapped_column(ForeignKey('agents.id',ondelete='CASCADE'),index=True); content:Mapped[str]=mapped_column(Text); namespace:Mapped[str]=mapped_column(String(160),index=True); metadata_json:Mapped[dict]=mapped_column('metadata',JSON,default=dict); tags:Mapped[list]=mapped_column(JSON,default=list); importance:Mapped[float]=mapped_column(Float,default=.5); expires_at:Mapped[datetime|None]=mapped_column(DateTime); archived:Mapped[bool]=mapped_column(Boolean,default=False,index=True); embedding:Mapped[list|None]=mapped_column(Vector(128)); created_at:Mapped[datetime]=mapped_column(DateTime,server_default=func.now(),index=True); updated_at:Mapped[datetime]=mapped_column(DateTime,server_default=func.now(),onupdate=func.now())
class ApiKey(Base):
    __tablename__='api_keys'; id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4); application_id:Mapped[uuid.UUID]=mapped_column(ForeignKey('applications.id',ondelete='CASCADE')); name:Mapped[str]=mapped_column(String(120)); key_hash:Mapped[str]=mapped_column(String(128),unique=True); prefix:Mapped[str]=mapped_column(String(20)); revoked:Mapped[bool]=mapped_column(Boolean,default=False); last_used_at:Mapped[datetime|None]=mapped_column(DateTime); created_at:Mapped[datetime]=mapped_column(DateTime,server_default=func.now())
class UsageLog(Base):
    __tablename__='usage_logs'; id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4); application_id:Mapped[uuid.UUID]=mapped_column(ForeignKey('applications.id',ondelete='CASCADE')); endpoint:Mapped[str]=mapped_column(String(160)); status_code:Mapped[int]=mapped_column(Integer); latency_ms:Mapped[float]=mapped_column(Float); created_at:Mapped[datetime]=mapped_column(DateTime,server_default=func.now(),index=True)
