from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL
from sqlalchemy.orm import relationship
from configure_db import Base
from datetime import datetime, timedelta


def pkt_now():
    return datetime.utcnow() + timedelta(hours=5)

class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    monthly_hit_limit = Column(Integer, nullable=False, default=0)
    allow_images = Column(Boolean, default=True)
    allow_pdfs = Column(Boolean, default=True)
    allow_structure = Column(Boolean, default=False)
    price = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    created_at = Column(DateTime, default=pkt_now)

    # ---------------- RELATIONSHIPS ---------------- #

    users = relationship("User", back_populates="plan")
    
    
    
