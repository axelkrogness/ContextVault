from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import String,Text,DateTime,ForeignKey,Float,Uuid
from sqlalchemy.orm import Mapped,mapped_column
from .db import Base

class User(Base):
 __tablename__="users"
 id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4)
 email:Mapped[str]=mapped_column(String(320),unique=True,index=True)
 password_hash:Mapped[str]=mapped_column(String(255))
 created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class Application(Base):
 __tablename__="applications"
 id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4)
 user_id:Mapped[UUID]=mapped_column(Uuid,ForeignKey("users.id"),index=True)
 name:Mapped[str]=mapped_column(String(200))
 created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class Agent(Base):
 __tablename__="agents"
 id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4)
 application_id:Mapped[UUID]=mapped_column(Uuid,ForeignKey("applications.id"),index=True)
 name:Mapped[str]=mapped_column(String(200))
 namespace:Mapped[str]=mapped_column(String(200),default="default")
 created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class Memory(Base):
 __tablename__="memories"
 id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4)
 agent_id:Mapped[UUID]=mapped_column(Uuid,ForeignKey("agents.id"),index=True)
 content:Mapped[str]=mapped_column(Text)
 tags:Mapped[str]=mapped_column(Text,default="")
 importance:Mapped[float]=mapped_column(Float,default=.5)
 created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
