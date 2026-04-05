from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ReleaseRegister(BaseModel):
    release_code: str
    git_commit: Optional[str] = None
    image_tag: str
    environment: str = Field(..., pattern="^(local|staging|production)$")
    notes: Optional[str] = None


class ReleaseResponse(BaseModel):
    id: str
    release_code: str
    git_commit: Optional[str]
    image_tag: str
    environment: str
    deployed_by_user_id: Optional[str]
    deployed_at: datetime
    status: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class JobResponse(BaseModel):
    id: str
    job_code: str
    job_type: str
    schedule_cron: Optional[str]
    is_active: bool
    last_run_at: Optional[datetime]
    last_status: Optional[str]
    last_duration_ms: Optional[int]
    last_error: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class JobRunResponse(BaseModel):
    id: str
    operational_job_id: str
    started_at: datetime
    finished_at: Optional[datetime]
    status: str
    output_summary: Optional[str]
    metadata_json: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class BackupRunResponse(BaseModel):
    backup_artifact_id: str
    status: str
    started_at: datetime


class BackupArtifactResponse(BaseModel):
    id: str
    backup_type: str
    artifact_path: str
    artifact_hash: Optional[str]
    size_bytes: Optional[int]
    started_at: datetime
    finished_at: Optional[datetime]
    status: str
    retention_until: Optional[datetime]
    verification_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class RestoreTestResponse(BaseModel):
    backup_artifact_id: str
    status: str
    verification_notes: Optional[str]


class HealthLiveResponse(BaseModel):
    status: str = "ok"


class HealthReadyResponse(BaseModel):
    app: str = Field(..., description="ready|not_ready")
    database: str = Field(..., description="ready|not_ready")
    redis: str = Field(..., description="ready|skipped|not_ready")
    storage: str = Field(..., description="ready|not_ready")
    version: str
    timestamp: datetime


class HealthDetailsResponse(BaseModel):
    app: str
    database: str
    redis: str
    storage: str
    version: str
    environment: str
    uptime_seconds: float
    timestamp: datetime


class HealthSnapshotResponse(BaseModel):
    id: str
    environment: str
    service_name: str
    health_status: str
    details_json: Optional[str]
    captured_at: datetime

    class Config:
        from_attributes = True


class RateLimitEventResponse(BaseModel):
    id: str
    actor_user_id: Optional[str]
    ip_address: Optional[str]
    route_key: str
    event_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConfigSummaryResponse(BaseModel):
    environment: str
    version: str
    database_url_configured: bool
    redis_configured: bool
    max_upload_size_mb: int
    rate_limit_enabled: bool
    feature_flags: Dict[str, bool]


class VersionResponse(BaseModel):
    version: str
    service: str = "buscamedicos-api"
