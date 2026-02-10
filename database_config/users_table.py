from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from configure_db import Base
from datetime import datetime, timedelta


def pkt_now():
    return datetime.utcnow() + timedelta(hours=5)


class User(Base):
    __tablename__ = "credentials"

    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(1024), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    created_at = Column(DateTime, default=pkt_now)
    
    # Relationship 
    
    plan = relationship("Plan", back_populates="users")
    api_keys = relationship("APISummary", back_populates="user", cascade="all, delete")
