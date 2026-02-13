from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, text
from sqlalchemy.orm import relationship
from Connections.database_connections import Base


class User(Base):
    __tablename__ = "credentials"

    user_id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(1024), nullable=False)

    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)

    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    # Relationships
    plan = relationship("Plan", back_populates="users")
    api_keys = relationship(
        "APISummary",
        back_populates="user",
        cascade="all, delete"
    )
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
