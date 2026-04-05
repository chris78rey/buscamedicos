"""step8 production hardening, operational tables and rate limiting

Revision ID: 007
Revises: 006
Create Date: 2024-01-08
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('deployment_releases',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('release_code', sa.String(), unique=True, nullable=False),
        sa.Column('git_commit', sa.String(), nullable=True),
        sa.Column('image_tag', sa.String(), nullable=False),
        sa.Column('environment', sa.String(), nullable=False),
        sa.Column('deployed_by_user_id', sa.String(), nullable=True),
        sa.Column('deployed_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('operational_jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('job_code', sa.String(), unique=True, nullable=False),
        sa.Column('job_type', sa.String(), nullable=False),
        sa.Column('schedule_cron', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('last_status', sa.String(), nullable=True),
        sa.Column('last_duration_ms', sa.BigInteger(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('operational_job_runs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('operational_job_id', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('output_summary', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_operational_job_runs_job_id'), 'operational_job_runs', ['operational_job_id'], unique=False)

    op.create_table('backup_artifacts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('backup_type', sa.String(), nullable=False),
        sa.Column('artifact_path', sa.Text(), nullable=False),
        sa.Column('artifact_hash', sa.String(), nullable=True),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('retention_until', sa.DateTime(), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('system_health_snapshots',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('environment', sa.String(), nullable=False),
        sa.Column('service_name', sa.String(), nullable=False),
        sa.Column('health_status', sa.String(), nullable=False),
        sa.Column('details_json', sa.Text(), nullable=True),
        sa.Column('captured_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('rate_limit_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('actor_user_id', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('route_key', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rate_limit_events_actor_user_id'), 'rate_limit_events', ['actor_user_id'], unique=False)
    op.create_index(op.f('ix_rate_limit_events_ip_address'), 'rate_limit_events', ['ip_address'], unique=False)

    op.add_column('audit_events', sa.Column('operational_scope', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('audit_events', sa.Column('release_code', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_table('rate_limit_events')
    op.drop_table('system_health_snapshots')
    op.drop_table('backup_artifacts')
    op.drop_table('operational_job_runs')
    op.drop_table('operational_jobs')
    op.drop_table('deployment_releases')
    op.drop_column('audit_events', 'release_code')
    op.drop_column('audit_events', 'operational_scope')
