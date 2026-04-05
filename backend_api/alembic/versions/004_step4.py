"""step4 teleconsultation and clinical records

Revision ID: 004
Revises: 003
Create Date: 2024-01-04

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add consultation_status to appointments
    op.add_column('appointments', sa.Column('consultation_status', sa.String(), nullable=True, server_default='not_started'))
    op.add_column('appointments', sa.Column('has_clinical_content', sa.Boolean(), nullable=True, server_default='false'))

    # teleconsultation_sessions
    op.create_table('teleconsultation_sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('appointment_id', sa.String(), nullable=False),
        sa.Column('provider_code', sa.String(), nullable=False),
        sa.Column('session_url', sa.Text(), nullable=False),
        sa.Column('host_url', sa.Text(), nullable=True),
        sa.Column('access_code', sa.String(), nullable=True),
        sa.Column('scheduled_start', sa.DateTime(), nullable=False),
        sa.Column('scheduled_end', sa.DateTime(), nullable=False),
        sa.Column('actual_start', sa.DateTime(), nullable=True),
        sa.Column('actual_end', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_by_user_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('appointment_id', name='uq_teleconsult_appointment')
    )
    op.create_index(op.f('ix_teleconsultation_sessions_appointment_id'), 'teleconsultation_sessions', ['appointment_id'], unique=False)

    # clinical_notes_simple
    op.create_table('clinical_notes_simple',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('appointment_id', sa.String(), nullable=False),
        sa.Column('professional_id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('note_status', sa.String(), nullable=False),
        sa.Column('reason_for_consultation', sa.Text(), nullable=True),
        sa.Column('subjective_summary', sa.Text(), nullable=True),
        sa.Column('objective_summary', sa.Text(), nullable=True),
        sa.Column('assessment', sa.Text(), nullable=True),
        sa.Column('plan', sa.Text(), nullable=True),
        sa.Column('private_professional_note', sa.Text(), nullable=True),
        sa.Column('visible_to_patient', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('appointment_id', name='uq_clinical_note_appointment')
    )
    op.create_index(op.f('ix_clinical_notes_simple_appointment_id'), 'clinical_notes_simple', ['appointment_id'], unique=False)

    # clinical_note_versions
    op.create_table('clinical_note_versions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinical_note_id', sa.String(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('snapshot_json', sa.Text(), nullable=False),
        sa.Column('changed_by_user_id', sa.String(), nullable=False),
        sa.Column('change_reason', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clinical_note_versions_clinical_note_id'), 'clinical_note_versions', ['clinical_note_id'], unique=False)

    # prescriptions
    op.create_table('prescriptions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('appointment_id', sa.String(), nullable=False),
        sa.Column('professional_id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('issued_at', sa.DateTime(), nullable=True),
        sa.Column('general_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prescriptions_appointment_id'), 'prescriptions', ['appointment_id'], unique=False)

    # prescription_items
    op.create_table('prescription_items',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('prescription_id', sa.String(), nullable=False),
        sa.Column('medication_name', sa.String(), nullable=False),
        sa.Column('presentation', sa.String(), nullable=True),
        sa.Column('dosage', sa.String(), nullable=False),
        sa.Column('frequency', sa.String(), nullable=False),
        sa.Column('duration', sa.String(), nullable=False),
        sa.Column('route', sa.String(), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prescription_items_prescription_id'), 'prescription_items', ['prescription_id'], unique=False)

    # care_instructions
    op.create_table('care_instructions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('appointment_id', sa.String(), nullable=False),
        sa.Column('professional_id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('follow_up_recommended', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('follow_up_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('appointment_id', name='uq_care_instructions_appointment')
    )
    op.create_index(op.f('ix_care_instructions_appointment_id'), 'care_instructions', ['appointment_id'], unique=False)

    # clinical_files
    op.create_table('clinical_files',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('appointment_id', sa.String(), nullable=False),
        sa.Column('uploaded_by_user_id', sa.String(), nullable=False),
        sa.Column('file_id', sa.String(), nullable=False),
        sa.Column('file_type', sa.String(), nullable=False),
        sa.Column('is_visible_to_patient', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('status', sa.String(), nullable=True, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clinical_files_appointment_id'), 'clinical_files', ['appointment_id'], unique=False)

    # clinical_access_audit
    op.create_table('clinical_access_audit',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=False),
        sa.Column('appointment_id', sa.String(), nullable=True),
        sa.Column('actor_user_id', sa.String(), nullable=False),
        sa.Column('actor_role_code', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clinical_access_audit_appointment_id'), 'clinical_access_audit', ['appointment_id'], unique=False)


def downgrade() -> None:
    op.drop_table('clinical_access_audit')
    op.drop_table('clinical_files')
    op.drop_table('care_instructions')
    op.drop_table('prescription_items')
    op.drop_table('prescriptions')
    op.drop_table('clinical_note_versions')
    op.drop_table('clinical_notes_simple')
    op.drop_table('teleconsultation_sessions')
    op.drop_column('appointments', 'has_clinical_content')
    op.drop_column('appointments', 'consultation_status')
