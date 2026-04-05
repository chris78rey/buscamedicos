import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, BigInteger
from app.core.database import Base


class ReleaseStatus:
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class DeploymentRelease(Base):
    __tablename__ = "deployment_releases"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    release_code = Column(String, unique=True, nullable=False)
    git_commit = Column(String, nullable=True)
    image_tag = Column(String, nullable=False)
    environment = Column(String, nullable=False)
    deployed_by_user_id = Column(String, nullable=True)
    deployed_at = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class JobType:
    BACKUP_DB = "backup_db"
    BACKUP_FILES = "backup_files"
    CLEANUP_TEMP = "cleanup_temp"
    EXPIRE_ACCESS = "expire_access"
    ROTATE_LOGS = "rotate_logs"
    RESTORE_TEST = "restore_test"


class JobStatus:
    SUCCESS = "success"
    FAILED = "failed"
    RUNNING = "running"


class OperationalJob(Base):
    __tablename__ = "operational_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_code = Column(String, unique=True, nullable=False)
    job_type = Column(String, nullable=False)
    schedule_cron = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime, nullable=True)
    last_status = Column(String, nullable=True)
    last_duration_ms = Column(BigInteger, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class OperationalJobRun(Base):
    __tablename__ = "operational_job_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    operational_job_id = Column(String, nullable=False)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)
    output_summary = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class BackupType:
    POSTGRES_DUMP = "postgres_dump"
    FILES_ARCHIVE = "files_archive"
    RESTORE_TEST_REPORT = "restore_test_report"


class BackupStatus:
    STARTED = "started"
    SUCCESS = "success"
    FAILED = "failed"
    VERIFIED = "verified"


class BackupArtifact(Base):
    __tablename__ = "backup_artifacts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    backup_type = Column(String, nullable=False)
    artifact_path = Column(Text, nullable=False)
    artifact_hash = Column(String, nullable=True)
    size_bytes = Column(BigInteger, nullable=True)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)
    retention_until = Column(DateTime, nullable=True)
    verification_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class HealthStatus:
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class SystemHealthSnapshot(Base):
    __tablename__ = "system_health_snapshots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    environment = Column(String, nullable=False)
    service_name = Column(String, nullable=False)
    health_status = Column(String, nullable=False)  # healthy, degraded, unhealthy
    details_json = Column(Text, nullable=True)
    captured_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class RateLimitEventType:
    THROTTLE = "throttle"
    BLOCK = "block"
    COOLDOWN = "cooldown"


class RateLimitEvent(Base):
    __tablename__ = "rate_limit_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_user_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    route_key = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")
