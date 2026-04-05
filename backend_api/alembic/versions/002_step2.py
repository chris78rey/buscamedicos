"""step2 initial schema

Revision ID: 002
Revises: 001
Create Date: 2024-01-02

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('specialties', sa.Column('id', sa.String(), nullable=False), sa.Column('code', sa.String(), nullable=False), sa.Column('name', sa.String(), nullable=False), sa.Column('description', sa.Text(), nullable=True), sa.Column('is_active', sa.Boolean(), nullable=True), sa.Column('created_at', sa.DateTime(), nullable=True), sa.Column('updated_at', sa.DateTime(), nullable=True), sa.Column('deleted_at', sa.DateTime(), nullable=True), sa.Column('version', sa.String(), nullable=True), primary_key=True)
    op.create_index(op.f('ix_specialties_code'), 'specialties', ['code'], unique=True)
    
    op.create_table('service_modalities', sa.Column('id', sa.String(), nullable=False), sa.Column('code', sa.String(), nullable=False), sa.Column('name', sa.String(), nullable=False), sa.Column('is_active', sa.Boolean(), nullable=True), sa.Column('created_at', sa.DateTime(), nullable=True), sa.Column('updated_at', sa.DateTime(), nullable=True), primary_key=True)
    op.create_index(op.f('ix_service_modalities_code'), 'service_modalities', ['code'], unique=True)
    
    op.create_table('professional_specialties', sa.Column('id', sa.String(), nullable=False), sa.Column('professional_id', sa.String(), nullable=False), sa.Column('specialty_id', sa.String(), nullable=False), sa.Column('is_primary', sa.Boolean(), nullable=True), sa.Column('created_at', sa.DateTime(), nullable=True), sa.Column('updated_at', sa.DateTime(), nullable=True), sa.Column('deleted_at', sa.DateTime(), nullable=True), sa.Column('version', sa.String(), nullable=True), sa.UniqueConstraint('professional_id', 'specialty_id', name='uq_professional_specialty'), primary_key=True)
    op.create_index(op.f('ix_professional_specialties_professional_id'), 'professional_specialties', ['professional_id'], unique=False)
    op.create_index(op.f('ix_professional_specialties_specialty_id'), 'professional_specialties', ['specialty_id'], unique=False)
    
    op.create_table('professional_modalities', sa.Column('id', sa.String(), nullable=False), sa.Column('professional_id', sa.String(), nullable=False), sa.Column('modality_id', sa.String(), nullable=False), sa.Column('is_enabled', sa.Boolean(), nullable=True), sa.Column('created_at', sa.DateTime(), nullable=True), sa.Column('updated_at', sa.DateTime(), nullable=True), sa.Column('deleted_at', sa.DateTime(), nullable=True), sa.Column('version', sa.String(), nullable=True), sa.UniqueConstraint('professional_id', 'modality_id', name='uq_professional_modality'), primary_key=True)
    op.create_index(op.f('ix_professional_modalities_professional_id'), 'professional_modalities', ['professional_id'], unique=False)
    op.create_index(op.f('ix_professional_modalities_modality_id'), 'professional_modalities', ['modality_id'], unique=False)
    
    op.create_table('professional_public_profiles', sa.Column('id', sa.String(), nullable=False), sa.Column('professional_id', sa.String(), nullable=False), sa.Column('public_title', sa.String(), nullable=False), sa.Column('public_bio', sa.Text(), nullable=True), sa.Column('consultation_price', sa.Numeric(precision=10, scale=2), nullable=True), sa.Column('currency_code', sa.String(length=3), nullable=True), sa.Column('province', sa.String(), nullable=True), sa.Column('city', sa.String(), nullable=True), sa.Column('sector', sa.String(), nullable=True), sa.Column('address_reference', sa.Text(), nullable=True), sa.Column('years_experience', sa.Integer(), nullable=True), sa.Column('languages_json', sa.Text(), nullable=True), sa.Column('is_public', sa.Boolean(), nullable=True), sa.Column('searchable_text', sa.Text(), nullable=True), sa.Column('created_at', sa.DateTime(), nullable=True), sa.Column('updated_at', sa.DateTime(), nullable=True), sa.Column('deleted_at', sa.DateTime(), nullable=True), sa.Column('version', sa.String(), nullable=True), primary_key=True)
    op.create_index(op.f('ix_professional_public_profiles_professional_id'), 'professional_public_profiles', ['professional_id'], unique=True)
    op.create_index(op.f('ix_professional_public_profiles_is_public'), 'professional_public_profiles', ['is_public'], unique=False)
    op.create_index(op.f('ix_professional_public_profiles_province'), 'professional_public_profiles', ['province'], unique=False)
    op.create_index(op.f('ix_professional_public_profiles_city'), 'professional_public_profiles', ['city'], unique=False)
    
    op.create_table('professional_availabilities', sa.Column('id', sa.String(), nullable=False), sa.Column('professional_id', sa.String(), nullable=False), sa.Column('weekday', sa.SmallInteger(), nullable=False), sa.Column('start_time', sa.Time(), nullable=False), sa.Column('end_time', sa.Time(), nullable=False), sa.Column('slot_minutes', sa.Integer(), nullable=False), sa.Column('modality_code', sa.String(), nullable=False), sa.Column('status', sa.String(), nullable=True), sa.Column('created_at', sa.DateTime(), nullable=True), sa.Column('updated_at', sa.DateTime(), nullable=True), sa.Column('deleted_at', sa.DateTime(), nullable=True), sa.Column('version', sa.String(), nullable=True), primary_key=True)
    op.create_index(op.f('ix_professional_availabilities_professional_id'), 'professional_availabilities', ['professional_id'], unique=False)
    op.create_index(op.f('ix_professional_availabilities_weekday_modality'), 'professional_availabilities', ['weekday', 'modality_code'], unique=False)
    
    op.create_table('professional_time_blocks', sa.Column('id', sa.String(), nullable=False), sa.Column('professional_id', sa.String(), nullable=False), sa.Column('starts_at', sa.DateTime(), nullable=False), sa.Column('ends_at', sa.DateTime(), nullable=False), sa.Column('reason', sa.String(), nullable=True), sa.Column('block_type', sa.String(), nullable=False), sa.Column('created_at', sa.DateTime(), nullable=True), sa.Column('updated_at', sa.DateTime(), nullable=True), sa.Column('deleted_at', sa.DateTime(), nullable=True), sa.Column('version', sa.String(), nullable=True), primary_key=True)
    op.create_index(op.f('ix_professional_time_blocks_professional_id'), 'professional_time_blocks', ['professional_id'], unique=False)
    op.create_index(op.f('ix_professional_time_blocks_starts_at'), 'professional_time_blocks', ['starts_at'], unique=False)
    op.create_index(op.f('ix_professional_time_blocks_ends_at'), 'professional_time_blocks', ['ends_at'], unique=False)
    
    op.create_table('appointments', sa.Column('id', sa.String(), nullable=False), sa.Column('public_code', sa.String(), nullable=False), sa.Column('patient_id', sa.String(), nullable=False), sa.Column('professional_id', sa.String(), nullable=False), sa.Column('modality_code', sa.String(), nullable=False), sa.Column('scheduled_start', sa.DateTime(), nullable=False), sa.Column('scheduled_end', sa.DateTime(), nullable=False), sa.Column('timezone', sa.String(), nullable=True), sa.Column('status', sa.String(), nullable=False), sa.Column('patient_note', sa.String(length=500), nullable=True), sa.Column('admin_note', sa.String(length=500), nullable=True), sa.Column('cancellation_reason', sa.String(length=300), nullable=True), sa.Column('reschedule_reason', sa.String(length=300), nullable=True), sa.Column('created_from', sa.String(), nullable=True), sa.Column('created_at', sa.DateTime(), nullable=True), sa.Column('updated_at', sa.DateTime(), nullable=True), sa.Column('deleted_at', sa.DateTime(), nullable=True), sa.Column('version', sa.String(), nullable=True), primary_key=True)
    op.create_index(op.f('ix_appointments_public_code'), 'appointments', ['public_code'], unique=True)
    op.create_index(op.f('ix_appointments_professional_id'), 'appointments', ['professional_id'], unique=False)
    op.create_index(op.f('ix_appointments_patient_id'), 'appointments', ['patient_id'], unique=False)
    op.create_index(op.f('ix_appointments_status'), 'appointments', ['status'], unique=False)
    op.create_index(op.f('ix_appointments_scheduled_start'), 'appointments', ['scheduled_start'], unique=False)
    
    op.create_table('appointment_status_history', sa.Column('id', sa.String(), nullable=False), sa.Column('appointment_id', sa.String(), nullable=False), sa.Column('old_status', sa.String(), nullable=True), sa.Column('new_status', sa.String(), nullable=False), sa.Column('changed_by_user_id', sa.String(), nullable=True), sa.Column('reason', sa.String(), nullable=True), sa.Column('created_at', sa.DateTime(), nullable=True), primary_key=True)
    op.create_index(op.f('ix_appointment_status_history_appointment_id'), 'appointment_status_history', ['appointment_id'], unique=False)
    
    op.create_table('professional_search_impressions', sa.Column('id', sa.String(), nullable=False), sa.Column('professional_id', sa.String(), nullable=False), sa.Column('viewer_user_id', sa.String(), nullable=True), sa.Column('search_session_id', sa.String(), nullable=True), sa.Column('position', sa.Integer(), nullable=False), sa.Column('created_at', sa.DateTime(), nullable=True), primary_key=True)
    op.create_index(op.f('ix_professional_search_impressions_professional_id'), 'professional_search_impressions', ['professional_id'], unique=False)


def downgrade() -> None:
    op.drop_table('professional_search_impressions')
    op.drop_table('appointment_status_history')
    op.drop_table('appointments')
    op.drop_table('professional_time_blocks')
    op.drop_table('professional_availabilities')
    op.drop_table('professional_public_profiles')
    op.drop_table('professional_modalities')
    op.drop_table('professional_specialties')
    op.drop_table('service_modalities')
    op.drop_table('specialties')