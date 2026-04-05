import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from app.core.database import Base
import enum

class RoleCode(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN_VALIDATION = "admin_validation"
    ADMIN_SUPPORT = "admin_support"
    PATIENT = "patient"
    PROFESSIONAL = "professional"

class UserRoleStatus(str, enum.Enum):
    ACTIVE = "active"
    REVOKED = "revoked"

class Role(Base):
    __tablename__ = "roles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    role_id = Column(String, nullable=False, index=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by = Column(String, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(String, nullable=True)
    status = Column(SQLEnum(UserRoleStatus), default=UserRoleStatus.ACTIVE)