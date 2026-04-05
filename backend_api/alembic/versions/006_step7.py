"""step7 privacy, exceptional access and data governance

Revision ID: 006
Revises: 005
Create Date: 2024-01-07

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('files', sa.Column('classification_code', sa.String(), nullable=True))
    op.add_column('files', sa.Column('retention_policy_id', sa.String(), nullable=True))
    op.add_column('files', sa.Column('legal_hold', sa.Boolean(), nullable=True, server_default='false'))

    op.create_table('data_classifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('code', sa.String(), unique=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('severity_level', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('resource_access_policies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), unique=True, nullable=False),
        sa.Column('classification_code', sa.String(), nullable=False),
        sa.Column('access_mode', sa.String(), nullable=False),
        sa.Column('requires_relationship', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('requires_patient_authorization', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('requires_justification', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('max_access_minutes', sa.Integer(), nullable=True),
        sa.Column('allow_download', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('patient_privacy_consents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('consent_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('evidence_file_id', sa.String(), nullable=True),
        sa.Column('granted_by_user_id', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_privacy_consents_patient_id'), 'patient_privacy_consents', ['patient_id'], unique=False)

    op.execute('DROP TABLE IF EXISTS exceptional_access_requests')
    op.create_table('exceptional_access_requests',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('requester_user_id', sa.String(), nullable=False),
        sa.Column('requester_role_code', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=True),
        sa.Column('target_user_id', sa.String(), nullable=True),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('scope_type', sa.String(), nullable=False),
        sa.Column('justification', sa.Text(), nullable=False),
        sa.Column('business_basis', sa.String(), nullable=True),
        sa.Column('requested_minutes', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('requires_patient_authorization', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('patient_consent_id', sa.String(), nullable=True),
        sa.Column('approved_by_user_id', sa.String(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('rejected_by_user_id', sa.String(), nullable=True),
        sa.Column('rejected_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('starts_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_by_user_id', sa.String(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('revoke_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exceptional_access_requests_requester_user_id'), 'exceptional_access_requests', ['requester_user_id'], unique=False)
    op.create_index(op.f('ix_exceptional_access_requests_patient_id'), 'exceptional_access_requests', ['patient_id'], unique=False)

    op.create_table('exceptional_access_grants',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('request_id', sa.String(), unique=True, nullable=False),
        sa.Column('grantee_user_id', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('scope_type', sa.String(), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exceptional_access_grants_grantee_user_id'), 'exceptional_access_grants', ['grantee_user_id'], unique=False)

    op.create_table('clinical_access_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('actor_user_id', sa.String(), nullable=False),
        sa.Column('actor_role_code', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=True),
        sa.Column('target_user_id', sa.String(), nullable=True),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('access_mode', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('decision', sa.String(), nullable=False),
        sa.Column('policy_snapshot_json', sa.Text(), nullable=True),
        sa.Column('exceptional_access_request_id', sa.String(), nullable=True),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clinical_access_logs_actor_user_id'), 'clinical_access_logs', ['actor_user_id'], unique=False)
    op.create_index(op.f('ix_clinical_access_logs_patient_id'), 'clinical_access_logs', ['patient_id'], unique=False)

    op.create_table('processing_activities',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('code', sa.String(), unique=True, nullable=False),
        sa.Column('module_name', sa.String(), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=False),
        sa.Column('data_categories_json', sa.Text(), nullable=False),
        sa.Column('subject_categories_json', sa.Text(), nullable=False),
        sa.Column('legal_basis', sa.Text(), nullable=True),
        sa.Column('retention_policy_id', sa.String(), nullable=True),
        sa.Column('is_sensitive', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('retention_policies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('code', sa.String(), unique=True, nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('retention_days', sa.Integer(), nullable=True),
        sa.Column('archive_after_days', sa.Integer(), nullable=True),
        sa.Column('delete_mode', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('privacy_incidents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('incident_code', sa.String(), unique=True, nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('reported_by_user_id', sa.String(), nullable=True),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('incident_type', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('affected_resource_type', sa.String(), nullable=True),
        sa.Column('affected_resource_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('assigned_admin_id', sa.String(), nullable=True),
        sa.Column('resolution_summary', sa.Text(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('privacy_incident_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('privacy_incident_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('event_payload_json', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_privacy_incident_events_incident_id'), 'privacy_incident_events', ['privacy_incident_id'], unique=False)

    op.create_table('privacy_policy_versions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('policy_type', sa.String(), nullable=False),
        sa.Column('version_code', sa.String(), nullable=False),
        sa.Column('content_markdown', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('policy_type', 'version_code', name='uq_policy_type_version')
    )

    op.create_table('privacy_policy_acceptances',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('policy_version_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), nullable=False),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_privacy_policy_acceptances_policy_version_id'), 'privacy_policy_acceptances', ['policy_version_id'], unique=False)
    op.create_index(op.f('ix_privacy_policy_acceptances_user_id'), 'privacy_policy_acceptances', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('privacy_policy_acceptances')
    op.drop_table('privacy_policy_versions')
    op.drop_table('privacy_incident_events')
    op.drop_table('privacy_incidents')
    op.drop_table('retention_policies')
    op.drop_table('processing_activities')
    op.drop_table('clinical_access_logs')
    op.drop_table('exceptional_access_grants')
    op.drop_table('exceptional_access_requests')
    op.drop_table('patient_privacy_consents')
    op.drop_table('resource_access_policies')
    op.drop_table('data_classifications')
    op.drop_column('files', 'legal_hold')
    op.drop_column('files', 'retention_policy_id')
    op.drop_column('files', 'classification_code')
