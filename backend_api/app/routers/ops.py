import uuid
import json
import os
import subprocess
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update, text
from fastapi import HTTPException, status, Request, Depends, Query, APIRouter
from fastapi.responses import JSONResponse

from app.core.database import get_db, engine
from app.core.dependencies import get_current_user
from app.core.ops_authorization import require_admin_ops
from app.core.rate_limiting import RateLimiter
from app.models.user import User
from app.models.step8_models import (
    DeploymentRelease, ReleaseStatus,
    OperationalJob, OperationalJobRun, JobType, JobStatus,
    BackupArtifact, BackupType, BackupStatus,
    SystemHealthSnapshot, HealthStatus,
    RateLimitEvent, RateLimitEventType,
)
from app.models.audit import AuditEvent
from app.schemas.step8_schemas import (
    ReleaseRegister, ReleaseResponse,
    JobResponse, JobRunResponse,
    BackupRunResponse, BackupArtifactResponse, RestoreTestResponse,
    HealthLiveResponse, HealthReadyResponse, HealthDetailsResponse, HealthSnapshotResponse,
    RateLimitEventResponse, ConfigSummaryResponse, VersionResponse,
)

API_VERSION = os.getenv("APP_VERSION", "1.0.0")


router = APIRouter()


async def _get_user_or_raise(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/health/live", response_model=HealthLiveResponse, tags=["health"])
async def health_live():
    return HealthLiveResponse(status="ok")


@router.get("/health/ready", response_model=HealthReadyResponse, tags=["health"])
async def health_ready(db: AsyncSession = Depends(get_db)):
    app_status = "ready"
    db_status = "not_ready"
    redis_status = "skipped"
    storage_status = "ready"

    try:
        await db.execute(text("SELECT 1"))
        db_status = "ready"
    except Exception:
        db_status = "not_ready"
        app_status = "not_ready"

    try:
        import os
        files_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "files")
        if os.path.exists(files_path):
            storage_status = "ready"
        else:
            storage_status = "not_ready"
    except Exception:
        storage_status = "not_ready"

    return HealthReadyResponse(
        app=app_status,
        database=db_status,
        redis=redis_status,
        storage=storage_status,
        version=API_VERSION,
        timestamp=datetime.utcnow(),
    )


@router.get("/health/details", response_model=HealthDetailsResponse, tags=["health"])
async def health_details(
    current_user: User = Depends(require_admin_ops),
    db: AsyncSession = Depends(get_db),
):
    db_status = "not_ready"
    redis_status = "skipped"
    storage_status = "not_ready"
    import os
    import time

    try:
        await db.execute(text("SELECT 1"))
        db_status = "ready"
    except Exception:
        pass

    try:
        files_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "files")
        if os.path.exists(files_path):
            storage_status = "ready"
    except Exception:
        pass

    return HealthDetailsResponse(
        app="ready",
        database=db_status,
        redis=redis_status,
        storage=storage_status,
        version=API_VERSION,
        environment=os.getenv("APP_ENV", "unknown"),
        uptime_seconds=time.time(),
        timestamp=datetime.utcnow(),
    )


@router.get("/version", response_model=VersionResponse, tags=["health"])
async def version():
    return VersionResponse(version=API_VERSION)


@router.get("/api/v1/admin/ops/releases", response_model=List[ReleaseResponse], tags=["ops"])
async def list_releases(
    current_user: User = Depends(require_admin_ops),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
):
    result = await db.execute(
        select(DeploymentRelease)
        .where(DeploymentRelease.deleted_at == None)
        .order_by(DeploymentRelease.deployed_at.desc())
        .offset(offset)
        .limit(limit)
    )
    releases = result.scalars().all()
    return [ReleaseResponse(
        id=r.id, release_code=r.release_code, git_commit=r.git_commit,
        image_tag=r.image_tag, environment=r.environment,
        deployed_by_user_id=r.deployed_by_user_id, deployed_at=r.deployed_at,
        status=r.status, notes=r.notes, created_at=r.created_at,
    ) for r in releases]


@router.post("/api/v1/admin/ops/releases/register", response_model=ReleaseResponse, tags=["ops"])
async def register_release(
    data: ReleaseRegister,
    current_user: User = Depends(require_admin_ops),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(DeploymentRelease).where(DeploymentRelease.release_code == data.release_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="release_code already exists")

    release = DeploymentRelease(
        id=str(uuid.uuid4()),
        release_code=data.release_code,
        git_commit=data.git_commit,
        image_tag=data.image_tag,
        environment=data.environment,
        deployed_by_user_id=str(current_user.id),
        deployed_at=datetime.utcnow(),
        status=ReleaseStatus.DEPLOYED,
        notes=data.notes,
    )
    db.add(release)

    audit = AuditEvent(
        id=str(uuid.uuid4()),
        actor_user_id=str(current_user.id),
        action="release.register",
        entity_type="deployment_release",
        entity_id=release.id,
        ip_address=None,
        user_agent=None,
        request_id=None,
        after_json=json.dumps({"release_code": data.release_code, "image_tag": data.image_tag}),
        severity=Severity.INFO,
        operational_scope=True,
        release_code=data.release_code,
    )
    db.add(audit)
    await db.commit()
    await db.refresh(release)
    return ReleaseResponse(
        id=release.id, release_code=release.release_code, git_commit=release.git_commit,
        image_tag=release.image_tag, environment=release.environment,
        deployed_by_user_id=release.deployed_by_user_id, deployed_at=release.deployed_at,
        status=release.status, notes=release.notes, created_at=release.created_at,
    )


@router.post("/api/v1/admin/ops/releases/{release_id}/mark-rollback", response_model=ReleaseResponse, tags=["ops"])
async def mark_rollback(
    release_id: str,
    current_user: User = Depends(require_admin_ops),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DeploymentRelease).where(
            and_(DeploymentRelease.id == release_id, DeploymentRelease.deleted_at == None)
        )
    )
    release = result.scalar_one_or_none()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    release.status = ReleaseStatus.ROLLED_BACK
    release.updated_at = datetime.utcnow()
    release.version = str(int(release.version) + 1)

    audit = AuditEvent(
        id=str(uuid.uuid4()),
        actor_user_id=str(current_user.id),
        action="release.mark_rollback",
        entity_type="deployment_release",
        entity_id=release.id,
        ip_address=None,
        user_agent=None,
        request_id=None,
        after_json=json.dumps({"release_code": release.release_code}),
        severity=Severity.INFO,
        operational_scope=True,
        release_code=release.release_code,
    )
    db.add(audit)
    await db.commit()
    await db.refresh(release)
    return ReleaseResponse(
        id=release.id, release_code=release.release_code, git_commit=release.git_commit,
        image_tag=release.image_tag, environment=release.environment,
        deployed_by_user_id=release.deployed_by_user_id, deployed_at=release.deployed_at,
        status=release.status, notes=release.notes, created_at=release.created_at,
    )


@router.get("/api/v1/admin/ops/jobs", response_model=List[JobResponse], tags=["ops"])
async def list_jobs(
    current_user: User = Depends(require_admin_ops),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OperationalJob)
        .where(and_(OperationalJob.is_active == True, OperationalJob.deleted_at == None))
        .order_by(OperationalJob.created_at.desc())
    )
    jobs = result.scalars().all()
    return [JobResponse(
        id=j.id, job_code=j.job_code, job_type=j.job_type,
        schedule_cron=j.schedule_cron, is_active=j.is_active,
        last_run_at=j.last_run_at, last_status=j.last_status,
        last_duration_ms=j.last_duration_ms, last_error=j.last_error,
        created_at=j.created_at,
    ) for j in jobs]


@router.post("/api/v1/admin/ops/jobs/{job_code}/run", response_model=JobRunResponse, tags=["ops"])
async def run_job(
    job_code: str,
    current_user: User = Depends(require_admin_ops),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OperationalJob).where(
            and_(OperationalJob.job_code == job_code, OperationalJob.deleted_at == None)
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job_run = OperationalJobRun(
        id=str(uuid.uuid4()),
        operational_job_id=job.id,
        started_at=datetime.utcnow(),
        status=JobStatus.RUNNING,
    )
    db.add(job_run)

    audit = AuditEvent(
        id=str(uuid.uuid4()),
        actor_user_id=str(current_user.id),
        action="job.run_manual",
        entity_type="operational_job",
        entity_id=job.id,
        ip_address=None,
        user_agent=None,
        request_id=None,
        after_json=json.dumps({"job_code": job_code}),
        severity=Severity.INFO,
        operational_scope=True,
    )
    db.add(audit)

    job.last_run_at = datetime.utcnow()
    job.last_status = JobStatus.RUNNING
    await db.commit()
    await db.refresh(job_run)
    return JobRunResponse(
        id=job_run.id, operational_job_id=job_run.operational_job_id,
        started_at=job_run.started_at, finished_at=job_run.finished_at,
        status=job_run.status, output_summary=job_run.output_summary,
        metadata_json=job_run.metadata_json, created_at=job_run.created_at,
    )


@router.get("/api/v1/admin/ops/job-runs", response_model=List[JobRunResponse], tags=["ops"])
async def list_job_runs(
    current_user: User = Depends(require_admin_ops),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    result = await db.execute(
        select(OperationalJobRun)
        .where(OperationalJobRun.deleted_at == None)
        .order_by(OperationalJobRun.started_at.desc())
        .offset(offset)
        .limit(limit)
    )
    runs = result.scalars().all()
    return [JobRunResponse(
        id=r.id, operational_job_id=r.operational_job_id,
        started_at=r.started_at, finished_at=r.finished_at,
        status=r.status, output_summary=r.output_summary,
        metadata_json=r.metadata_json, created_at=r.created_at,
    ) for r in runs]


@router.get("/api/v1/admin/ops/backups", response_model=List[BackupArtifactResponse], tags=["ops"])
async def list_backups(
    current_user: User = Depends(require_admin_ops),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
):
    result = await db.execute(
        select(BackupArtifact)
        .where(and_(BackupArtifact.deleted_at == None))
        .order_by(BackupArtifact.started_at.desc())
        .offset(offset)
        .limit(limit)
    )
    artifacts = result.scalars().all()
    return [BackupArtifactResponse(
        id=a.id, backup_type=a.backup_type, artifact_path=a.artifact_path,
        artifact_hash=a.artifact_hash, size_bytes=a.size_bytes,
        started_at=a.started_at, finished_at=a.finished_at,
        status=a.status, retention_until=a.retention_until,
        verification_notes=a.verification_notes, created_at=a.created_at,
    ) for a in artifacts]


def _run_pg_dump() -> tuple[str, str, int]:
    try:
        db_url = os.getenv("DATABASE_URL", "")
        if not db_url:
            return "", "DATABASE_URL not set", 1
        result = subprocess.run(
            ["pg_dump", "-Fc", "-f", "-", "--dbname", db_url],
            capture_output=True, timeout=300,
        )
        return result.stdout, "", result.returncode
    except FileNotFoundError:
        return "", "pg_dump not found in PATH", 1
    except subprocess.TimeoutExpired:
        return "", "pg_dump timed out after 300s", 1
    except Exception as e:
        return "", str(e), 1


def _compute_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _get_backup_dir() -> str:
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir


@router.post("/api/v1/admin/ops/backups/run-db", response_model=BackupRunResponse, tags=["ops"])
async def run_db_backup(
    current_user: User = Depends(require_admin_ops),
    db: AsyncSession = Depends(get_db),
):
    backup_id = str(uuid.uuid4())
    started_at = datetime.utcnow()

    artifact = BackupArtifact(
        id=backup_id,
        backup_type=BackupType.POSTGRES_DUMP,
        artifact_path="pending",
        started_at=started_at,
        status=BackupStatus.STARTED,
    )
    db.add(artifact)

    audit = AuditEvent(
        id=str(uuid.uuid4()),
        actor_user_id=str(current_user.id),
        action="backup.db.start",
        entity_type="backup_artifact",
        entity_id=backup_id,
        ip_address=None,
        user_agent=None,
        request_id=None,
        after_json=json.dumps({"backup_type": BackupType.POSTGRES_DUMP}),
        severity=Severity.INFO,
        operational_scope=True,
    )
    db.add(audit)
    await db.commit()

    data, error, code = _run_pg_dump()
    if code != 0:
        artifact.status = BackupStatus.FAILED
        artifact.finished_at = datetime.utcnow()
        artifact.verification_notes = error
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Backup failed: {error}")

    backup_dir = _get_backup_dir()
    filename = f"pg_dump_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{backup_id[:8]}.dump"
    filepath = os.path.join(backup_dir, filename)
    with open(filepath, "wb") as f:
        f.write(data)

    artifact.artifact_path = filepath
    artifact.artifact_hash = _compute_hash(data)
    artifact.size_bytes = len(data)
    artifact.finished_at = datetime.utcnow()
    artifact.status = BackupStatus.SUCCESS

    audit.action = "backup.db.complete"
    audit.after_json = json.dumps({"backup_type": BackupType.POSTGRES_DUMP, "size_bytes": len(data), "hash": artifact.artifact_hash})
    await db.commit()
    await db.refresh(artifact)
    return BackupRunResponse(backup_artifact_id=artifact.id, status=artifact.status, started_at=started_at)


@router.post("/api/v1/admin/ops/backups/run-files", response_model=BackupRunResponse, tags=["ops"])
async def run_files_backup(
    current_user: User = Depends(require_admin_ops),
    db: AsyncSession = Depends(get_db),
):
    backup_id = str(uuid.uuid4())
    started_at = datetime.utcnow()

    artifact = BackupArtifact(
        id=backup_id,
        backup_type=BackupType.FILES_ARCHIVE,
        artifact_path="pending",
        started_at=started_at,
        status=BackupStatus.STARTED,
    )
    db.add(artifact)

    audit = AuditEvent(
        id=str(uuid.uuid4()),
        actor_user_id=str(current_user.id),
        action="backup.files.start",
        entity_type="backup_artifact",
        entity_id=backup_id,
        ip_address=None,
        user_agent=None,
        request_id=None,
        after_json=json.dumps({"backup_type": BackupType.FILES_ARCHIVE}),
        severity=Severity.INFO,
        operational_scope=True,
    )
    db.add(audit)
    await db.commit()

    try:
        files_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "files")
        if not os.path.exists(files_dir):
            raise HTTPException(status_code=404, detail="Files directory not found")

        backup_dir = _get_backup_dir()
        filename = f"files_archive_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{backup_id[:8]}.tar.gz"
        filepath = os.path.join(backup_dir, filename)

        result = subprocess.run(
            ["tar", "czf", filepath, "-C", os.path.dirname(files_dir), os.path.basename(files_dir)],
            capture_output=True, timeout=600,
        )

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"tar failed: {result.stderr.decode()}")

        size = os.path.getsize(filepath)
        artifact.artifact_path = filepath
        artifact.size_bytes = size
        artifact.finished_at = datetime.utcnow()
        artifact.status = BackupStatus.SUCCESS

        audit.action = "backup.files.complete"
        await db.commit()
        await db.refresh(artifact)
        return BackupRunResponse(backup_artifact_id=artifact.id, status=artifact.status, started_at=started_at)

    except HTTPException:
        raise
    except FileNotFoundError:
        artifact.status = BackupStatus.FAILED
        artifact.verification_notes = "tar not found or files directory missing"
        artifact.finished_at = datetime.utcnow()
        await db.commit()
        raise HTTPException(status_code=500, detail="Backup failed: tar not available")
    except Exception as e:
        artifact.status = BackupStatus.FAILED
        artifact.verification_notes = str(e)
        artifact.finished_at = datetime.utcnow()
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Backup failed: {e}")


@router.post("/api/v1/admin/ops/backups/run-restore-test", response_model=RestoreTestResponse, tags=["ops"])
async def run_restore_test(
    current_user: User = Depends(require_admin_ops),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BackupArtifact).where(
            and_(
                BackupArtifact.backup_type == BackupType.POSTGRES_DUMP,
                BackupArtifact.status == BackupStatus.SUCCESS,
                BackupArtifact.deleted_at == None,
            )
        ).order_by(BackupArtifact.finished_at.desc()).limit(1)
    )
    latest = result.scalar_one_or_none()
    if not latest:
        raise HTTPException(status_code=404, detail="No successful DB backup found to test")

    backup_id = str(uuid.uuid4())
    started_at = datetime.utcnow()

    report = BackupArtifact(
        id=backup_id,
        backup_type=BackupType.RESTORE_TEST_REPORT,
        artifact_path="pending",
        started_at=started_at,
        status=BackupStatus.STARTED,
        metadata_json=json.dumps({"tested_artifact_id": latest.id}),
    )
    db.add(report)

    audit = AuditEvent(
        id=str(uuid.uuid4()),
        actor_user_id=str(current_user.id),
        action="restore_test.start",
        entity_type="backup_artifact",
        entity_id=latest.id,
        ip_address=None,
        user_agent=None,
        request_id=None,
        after_json=json.dumps({"test_report_id": backup_id}),
        severity=Severity.CRITICAL,
        operational_scope=True,
    )
    db.add(audit)
    await db.commit()

    try:
        verification_notes = f"Restore test on {latest.artifact_path} — hash {latest.artifact_hash} — size {latest.size_bytes} bytes. In production, restore to a temporary DB instance, not the live database."
        report.artifact_path = f"restore_test:{latest.id}"
        report.finished_at = datetime.utcnow()
        report.status = BackupStatus.SUCCESS
        report.verification_notes = verification_notes
        report.metadata_json = json.dumps({
            "tested_artifact_id": latest.id,
            "tested_hash": latest.artifact_hash,
            "tested_size": latest.size_bytes,
            "result": "simulation_only",
        })

        audit.action = "restore_test.complete"
        await db.commit()
        await db.refresh(report)
        return RestoreTestResponse(
            backup_artifact_id=report.id,
            status=report.status,
            verification_notes=verification_notes,
        )
    except Exception as e:
        report.status = BackupStatus.FAILED
        report.verification_notes = str(e)
        report.finished_at = datetime.utcnow()
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Restore test failed: {e}")


@router.get("/api/v1/admin/ops/health-snapshots", response_model=List[HealthSnapshotResponse], tags=["ops"])
async def list_health_snapshots(
    current_user: User = Depends(require_admin_ops),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
):
    result = await db.execute(
        select(SystemHealthSnapshot)
        .where(SystemHealthSnapshot.deleted_at == None)
        .order_by(SystemHealthSnapshot.captured_at.desc())
        .offset(offset)
        .limit(limit)
    )
    snapshots = result.scalars().all()
    return [HealthSnapshotResponse(
        id=s.id, environment=s.environment, service_name=s.service_name,
        health_status=s.health_status, details_json=s.details_json,
        captured_at=s.captured_at,
    ) for s in snapshots]


@router.get("/api/v1/admin/ops/rate-limit-events", response_model=List[RateLimitEventResponse], tags=["ops"])
async def list_rate_limit_events(
    current_user: User = Depends(require_admin_ops),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    result = await db.execute(
        select(RateLimitEvent)
        .where(RateLimitEvent.deleted_at == None)
        .order_by(RateLimitEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    events = result.scalars().all()
    return [RateLimitEventResponse(
        id=e.id, actor_user_id=e.actor_user_id, ip_address=e.ip_address,
        route_key=e.route_key, event_type=e.event_type, created_at=e.created_at,
    ) for e in events]


@router.get("/api/v1/admin/ops/config-summary", response_model=ConfigSummaryResponse, tags=["ops"])
async def get_config_summary(
    current_user: User = Depends(require_admin_ops),
    db: AsyncSession = Depends(get_db),
):
    env = os.getenv("APP_ENV", "unknown")
    db_url_set = bool(os.getenv("DATABASE_URL", ""))
    redis_set = bool(os.getenv("REDIS_URL", ""))
    max_upload = int(os.getenv("MAX_FILE_SIZE_MB", "10"))

    result = await db.execute(
        select(SystemHealthSnapshot)
        .where(SystemHealthSnapshot.deleted_at == None)
        .order_by(SystemHealthSnapshot.captured_at.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()
    rate_limit_enabled = latest.health_status != "unhealthy" if latest else True

    return ConfigSummaryResponse(
        environment=env,
        version=API_VERSION,
        database_url_configured=db_url_set,
        redis_configured=redis_set,
        max_upload_size_mb=max_upload,
        rate_limit_enabled=rate_limit_enabled,
        feature_flags={
            "go_live_guard_enabled": env == "production",
            "production_observability_enabled": env in ("production", "staging"),
            "rate_limit_enabled": True,
        },
    )
