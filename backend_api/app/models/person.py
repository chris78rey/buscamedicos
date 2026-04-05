import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.core.database import Base

class Person(Base):
    __tablename__ = "people"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    last_name = Column(String, nullable=False)
    second_last_name = Column(String, nullable=True)
    national_id = Column(String, nullable=False, index=True)
    phone = Column(String, nullable=False)
    birth_date = Column(DateTime, nullable=True)
    sex = Column(String, nullable=True)
    country = Column(String, default="Ecuador")
    province = Column(String, nullable=True)
    city = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    deleted_by = Column(String, nullable=True)
    version = Column(String, default="1")