from sqlalchemy import Column, Integer, String
from configure_db import Base

class User(Base):
    __tablename__ = "credentials"

    user_id = Column(Integer, primary_key=True)
    full_name = Column(String(50))
    email = Column(String(50), unique=True)
    password = Column(String(1050))

