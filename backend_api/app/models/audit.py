import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text
from app.core.database import Base
import enum

class Severity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    occurred_at = Column(DateTime, default=datetime.utcnow, index=True)
    actor_user_id = Column(String, nullable=True, index=True)
    actor_role_code = Column(String, nullable=True)
    action = Column(String, nullable=False, index=True)
    resource_type = Column(String, nullable=False, index=True)
    resource_id = Column(String, nullable=False, index=True)
    request_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    metadata_json = Column(Text, nullable=True)
    details_json = Column(Text, nullable=True)
    justification = Column(Text, nullable=True)
    severity = Column(SQLEnum(Severity), default=Severity.INFO)
    operational_scope = Column(String, nullable=True)
    release_code = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)