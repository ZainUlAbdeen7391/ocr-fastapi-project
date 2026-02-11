from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL, text
from sqlalchemy.orm import relationship
from configure_db import Base
from datetime import datetime, timedelta


def pkt_now():
    return datetime.utcnow() + timedelta(hours=5)


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

    monthly_hit_limit = Column(Integer, nullable=False)

    # DATABASE controls defaults
    allow_images = Column(Boolean, nullable=False, server_default=text("1"))
    allow_pdfs = Column(Boolean, nullable=False, server_default=text("1"))
    allow_structure = Column(Boolean, nullable=False, server_default=text("0"))

    price = Column(DECIMAL(10, 2), nullable=False, server_default=text("0.00"))

    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    users = relationship("User", back_populates="plan")
