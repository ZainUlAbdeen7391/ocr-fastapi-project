from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL
from configure_db import Base
from datetime import datetime

class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(50), unique=True, nullable=False)

    monthly_hit_limit = Column(Integer, nullable=False)

    allow_images = Column(Boolean, default=True)
    allow_pdfs = Column(Boolean, default=True)
    allow_structure = Column(Boolean, default=False)

    price = Column(DECIMAL(10, 2), default=0.00)

    created_at = Column(DateTime, default=datetime.utcnow)
    
    
    
    
    
    
    
    
    
    
    
    
