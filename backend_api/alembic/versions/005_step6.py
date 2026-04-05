"""step6 reviews, reports, moderation and sanctions

Revision ID: 005
Revises: 004
Create Date: 2024-01-06

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('appointments', sa.Column('patient_review_submitted', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('appointments', sa.Column('professional_review_submitted', sa.Boolean(), nullable=True, server_default='false'))

    op.create_table('appointment_reviews',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('appointment_id', sa.String(), nullable=False),
        sa.Column('reviewer_user_id', sa.String(), nullable=False),
        sa.Column('reviewer_role_code', sa.String(), nullable=False),
        sa.Column('target_user_id', sa.String(), nullable=False),
        sa.Column('target_role_code', sa.String(), nullable=False),
        sa.Column('rating_overall', sa.SmallInteger(), nullable=False),
        sa.Column('rating_punctuality', sa.SmallInteger(), nullable=True),
        sa.Column('rating_communication', sa.SmallInteger(), nullable=True),
        sa.Column('rating_respect', sa.SmallInteger(), nullable=True),
        sa.Column('comment_text', sa.Text(), nullable=True),
        sa.Column('visibility', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('moderation_flag', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('appointment_id', 'reviewer_user_id', 'target_user_id', name='uq_review_per_direction')
    )
    op.create_index(op.f('ix_appointment_reviews_appointment_id'), 'appointment_reviews', ['appointment_id'], unique=False)
    op.create_index(op.f('ix_appointment_reviews_reviewer_user_id'), 'appointment_reviews', ['reviewer_user_id'], unique=False)
    op.create_index(op.f('ix_appointment_reviews_target_user_id'), 'appointment_reviews', ['target_user_id'], unique=False)

    op.create_table('appointment_review_versions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('review_id', sa.String(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('snapshot_json', sa.Text(), nullable=False),
        sa.Column('changed_by_user_id', sa.String(), nullable=False),
        sa.Column('change_reason', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_appointment_review_versions_review_id'), 'appointment_review_versions', ['review_id'], unique=False)

    op.create_table('professional_reputation_stats',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('professional_id', sa.String(), nullable=False),
        sa.Column('public_reviews_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('avg_overall', sa.Numeric(precision=4, scale=2), nullable=True, server_default='0'),
        sa.Column('avg_punctuality', sa.Numeric(precision=4, scale=2), nullable=True, server_default='0'),
        sa.Column('avg_communication', sa.Numeric(precision=4, scale=2), nullable=True, server_default='0'),
        sa.Column('avg_respect', sa.Numeric(precision=4, scale=2), nullable=True, server_default='0'),
        sa.Column('hidden_reviews_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_calculated_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('professional_id', name='uq_reputation_professional')
    )

    op.create_table('safety_reports',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('reporter_user_id', sa.String(), nullable=False),
        sa.Column('subject_type', sa.String(), nullable=False),
        sa.Column('subject_id', sa.String(), nullable=False),
        sa.Column('appointment_id', sa.String(), nullable=True),
        sa.Column('category_code', sa.String(), nullable=False),
        sa.Column('severity_claimed', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('is_counterparty_hidden', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
        sa.Column('assigned_admin_id', sa.String(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_safety_reports_reporter_user_id'), 'safety_reports', ['reporter_user_id'], unique=False)
    op.create_index(op.f('ix_safety_reports_subject_id'), 'safety_reports', ['subject_id'], unique=False)
    op.create_index(op.f('ix_safety_reports_appointment_id'), 'safety_reports', ['appointment_id'], unique=False)

    op.create_table('safety_report_evidences',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('report_id', sa.String(), nullable=False),
        sa.Column('file_id', sa.String(), nullable=False),
        sa.Column('evidence_type', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_safety_report_evidences_report_id'), 'safety_report_evidences', ['report_id'], unique=False)

    op.create_table('moderation_cases',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=True),
        sa.Column('target_type', sa.String(), nullable=False),
        sa.Column('target_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('priority', sa.String(), nullable=False),
        sa.Column('assigned_admin_id', sa.String(), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=False),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('outcome_code', sa.String(), nullable=True),
        sa.Column('outcome_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_moderation_cases_target_id'), 'moderation_cases', ['target_id'], unique=False)

    op.create_table('moderation_case_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('moderation_case_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('event_payload_json', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_moderation_case_events_case_id'), 'moderation_case_events', ['moderation_case_id'], unique=False)

    op.create_table('account_sanctions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('target_type', sa.String(), nullable=False),
        sa.Column('target_id', sa.String(), nullable=False),
        sa.Column('sanction_type', sa.String(), nullable=False),
        sa.Column('reason_code', sa.String(), nullable=False),
        sa.Column('reason_text', sa.Text(), nullable=True),
        sa.Column('starts_at', sa.DateTime(), nullable=False),
        sa.Column('ends_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('applied_by_user_id', sa.String(), nullable=False),
        sa.Column('lifted_by_user_id', sa.String(), nullable=True),
        sa.Column('lifted_reason', sa.Text(), nullable=True),
        sa.Column('moderation_case_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_account_sanctions_target_id'), 'account_sanctions', ['target_id'], unique=False)

    op.create_table('trust_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('target_type', sa.String(), nullable=False),
        sa.Column('target_id', sa.String(), nullable=False),
        sa.Column('event_code', sa.String(), nullable=False),
        sa.Column('weight', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trust_events_target_id'), 'trust_events', ['target_id'], unique=False)


def downgrade() -> None:
    op.drop_table('trust_events')
    op.drop_table('account_sanctions')
    op.drop_table('moderation_case_events')
    op.drop_table('moderation_cases')
    op.drop_table('safety_report_evidences')
    op.drop_table('safety_reports')
    op.drop_table('professional_reputation_stats')
    op.drop_table('appointment_review_versions')
    op.drop_table('appointment_reviews')
    op.drop_column('appointments', 'professional_review_submitted')
    op.drop_column('appointments', 'patient_review_submitted')
