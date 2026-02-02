from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from configure_db import Base

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("credentials.user_id"))
    api_key = Column(String(255), unique=True)
    total_hits = Column(Integer, default=2)
    used_hits = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    