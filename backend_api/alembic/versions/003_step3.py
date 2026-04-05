"""step3 payments and settlements

Revision ID: 003
Revises: 002
Create Date: 2024-01-03

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('appointments', sa.Column('financial_status', sa.String(), nullable=True, server_default='unpaid'))
    
    op.create_table('pricing_policies', sa.Column('id', sa.String(), nullable=False), sa.Column('code', sa.String(), nullable=False), sa.Column('name', sa.String(), nullable=False), sa.Column('commission_type', sa.String(), nullable=False), sa.Column('commission_value', sa.Numeric(precision=10, scale=2), nullable=False), sa.Column('is_active', sa.Boolean(), nullable=True), sa.Column('created_at', sa.DateTime(), nullable=True), sa.Column('updated_at', sa.DateTime(), nullable=True), sa.Column('deleted_at', sa.DateTime(), nullable=True), sa.Column('version', sa.String(), nullable=True), primary_key=True)
    op.create_index(op.f('ix_pricing_policies_code'), 'pricing_policies', ['code'], unique=True)
    
    op.create_table('professional_prices', sa.Column('id', sa.String(), nullable=False), sa.Column('professional_id', sa.String(), nullable=False), sa.Column('modality_code', sa.String(), nullable=False), sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False), sa.Column('currency_code', sa.String(length=3), nullable=True), sa.Column('pricing_policy_id', sa.String(), nullable=False), sa.Column('is_active', sa.Boolean(), nullable=True), sa.Column('created_at', sa.DateTime(), nullable=True), sa.Column('updated_at', sa.DateTime(), nullable=True), sa.Column('deleted_at', sa.DateTime(), nullable=True), sa.Column('version', sa.String(), nullable=True), sa.UniqueConstraint('professional_id', 'modality_code', name='uq_professional_modality_price'), primary_key=True)
    op.create_index(op.f('ix_professional_prices_professional_id'), 'professional_prices', ['professional_id'], unique=False)
    
    op.create_table('payment_intents', sa.Column('id', sa.String(), nullable=False), sa.Column('appointment_id', sa.String(), nullable=False), sa.Column('patient_id', sa.String(), nullable=False), sa.Column('amount_total', sa.Numeric(precision=10, scale=2), nullable=False), sa.Column('currency_code', sa.String(length=3), nullable=True), sa.Column('status', sa.String(), nullable=False), sa.Column('provider_code', sa.String(), nullable=False), sa.Column('provider_reference', sa.String(), nullable=True), sa.Column('idempotency_key', sa.String(), nullable=False), sa.Column('expires_at', sa.DateTime(), nullable=True), sa.Column('created_at', sa.DateTime(), nullable=True), sa.Column('updated_at', sa.DateTime(), nullable=True), sa.Column('deleted_at', sa.DateTime(), nullable=True), sa.Column('version', sa.String(), nullable=True), primary_key=True)
    op.create_index(op.f('ix_payment_intents_idempotency_key'), 'payment_intents', ['idempotency_key'], unique=True)
    op.create_index(op.f('ix_payment_intents_appointment_id'), 'payment_intents', ['appointment_id'], unique=False)
    op.create_index(op.f('ix_payment_intents_patient_id'), 'payment_intents', ['patient_id'], unique=False)
    
    op.create_table('payments', sa.Column('id', sa.String(), nullable=False), sa.Column('payment_intent_id', sa.String(), nullable=False), sa.Column('appointment_id', sa.String(), nullable=False), sa.Column('patient_id', sa.String(), nullable=False), sa.Column('amount_total', sa.Numeric(precision=10, scale=2), nullable=False), sa.Column('currency_code', sa.String(length=3), nullable=False), sa.Column('status', sa.String(), nullable=False), sa.Column('paid_at', sa.DateTime(), nullable=True), sa.Column('external_reference', sa.String(), nullable=True), sa.Column('reconciliation_status', sa.String(), nullable=True), sa.Column('created_at', sa.DateTime(), nullable=True), sa.Column('updated_at', sa.DateTime(), nullable=True), sa.Column('deleted_at', sa.DateTime(), nullable=True), sa.Column('version', sa.String(), nullable=True), primary_key=True)
    op.create_index(op.f('ix_payments_payment_intent_id'), 'payments', ['payment_intent_id'], unique=True)
    op.create_index(op.f('ix_payments_appointment_id'), 'payments', ['appointment_id'], unique=False)
    
    op.create_table('payment_transactions', sa.Column('id', sa.String(), nullable=False), sa.Column('payment_id', sa.String(), nullable=True), sa.Column('payment_intent_id', sa.String(), nullable=True), sa.Column('transaction_type', sa.String(), nullable=False), sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False), sa.Column('currency_code', sa.String(length=3), nullable=False), sa.Column('provider_code', sa.String(), nullable=False), sa.Column('provider_reference', sa.String(), nullable=True), sa.Column('raw_response_json', sa.Text(), nullable=True), sa.Column('status', sa.String(), nullable=False), sa.Column('created_at', sa.DateTime(), nullable=True), sa.Column('created_by', sa.String(), nullable=True), primary_key=True)
    op.create_index(op.f('ix_payment_transactions_payment_id'), 'payment_transactions', ['payment_id'], unique=False)
    
    op.create_table('appointment_financials', sa.Column('id', sa.String(), nullable=False), sa.Column('appointment_id', sa.String(), nullable=False), sa.Column('professional_price_id', sa.String(), nullable=False), sa.Column('gross_amount', sa.Numeric(precision=10, scale=2), nullable=False), sa.Column('platform_commission_type', sa.String(), nullable=False), sa.Column('platform_commission_value', sa.Numeric(precision=10, scale=2), nullable=False), sa.Column('platform_commission_amount', sa.Numeric(precision=10, scale=2), nullable=False), sa.Column('professional_net_amount', sa.Numeric(precision=10, scale=2), nullable=False), sa.Column('currency_code', sa.String(length=3), nullable=True), sa.Column('payment_status', sa.String(), nullable=False), sa.Column('settlement_status', sa.String(), nullable=False), sa.Column('created_at', sa.DateTime(), nullable=True), sa.Column('updated_at', sa.DateTime(), nullable=True), sa.Column('deleted_at', sa.DateTime(), nullable=True), sa.Column('version', sa.String(), nullable=True), primary_key=True)
    op.create_index(op.f('ix_appointment_financials_appointment_id'), 'appointment_financials', ['appointment_id'], unique=True)
    
    op.create_table('refunds', sa.Column('id', sa.String(), nullable=False), sa.Column('payment_id', sa.String(), nullable=False), sa.Column('appointment_id', sa.String(), nullable=False), sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False), sa.Column('currency_code', sa.String(length=3), nullable=False), sa.Column('reason', sa.String(), nullable=False), sa.Column('status', sa.String(), nullable=False), sa.Column('requested_by_user_id', sa.String(), nullable=True), sa.Column('approved_by_user_id', sa.String(), nullable=True), sa.Column('created_at', sa.DateTime(), nullable=True), sa.Column('updated_at', sa.DateTime(), nullable=True), sa.Column('deleted_at', sa.DateTime(), nullable=True), sa.Column('version', sa.String(), nullable=True), primary_key=True)
    op.create_index(op.f('ix_refunds_payment_id'), 'refunds', ['payment_id'], unique=False)
    op.create_index(op.f('ix_refunds_appointment_id'), 'refunds', ['appointment_id'], unique=False)
    
    op.create_table('settlement_batches', sa.Column('id', sa.String(), nullable=False), sa.Column('batch_code', sa.String(), nullable=False), sa.Column('professional_id', sa.String(), nullable=False), sa.Column('total_gross', sa.Numeric(precision=10, scale=2), nullable=False), sa.Column('total_commission', sa.Numeric(precision=10, scale=2), nullable=False), sa.Column('total_net', sa.Numeric(precision=10, scale=2), nullable=False), sa.Column('currency_code', sa.String(length=3), nullable=True), sa.Column('status', sa.String(), nullable=False), sa.Column('generated_at', sa.DateTime(), nullable=True), sa.Column('paid_at', sa.DateTime(), nullable=True), sa.Column('created_at', sa.DateTime(), nullable=True), sa.Column('updated_at', sa.DateTime(), nullable=True), sa.Column('deleted_at', sa.DateTime(), nullable=True), sa.Column('version', sa.String(), nullable=True), primary_key=True)
    op.create_index(op.f('ix_settlement_batches_batch_code'), 'settlement_batches', ['batch_code'], unique=True)
    op.create_index(op.f('ix_settlement_batches_professional_id'), 'settlement_batches', ['professional_id'], unique=False)
    
    op.create_table('settlement_batch_items', sa.Column('id', sa.String(), nullable=False), sa.Column('settlement_batch_id', sa.String(), nullable=False), sa.Column('appointment_id', sa.String(), nullable=False), sa.Column('appointment_financial_id', sa.String(), nullable=False), sa.Column('gross_amount', sa.Numeric(precision=10, scale=2), nullable=False), sa.Column('commission_amount', sa.Numeric(precision=10, scale=2), nullable=False), sa.Column('net_amount', sa.Numeric(precision=10, scale=2), nullable=False), sa.Column('created_at', sa.DateTime(), nullable=True), primary_key=True)
    op.create_index(op.f('ix_settlement_batch_items_batch_id'), 'settlement_batch_items', ['settlement_batch_id'], unique=False)


def downgrade() -> None:
    op.drop_column('appointments', 'financial_status')
    op.drop_table('settlement_batch_items')
    op.drop_table('settlement_batches')
    op.drop_table('refunds')
    op.drop_table('appointment_financials')
    op.drop_table('payment_transactions')
    op.drop_table('payments')
    op.drop_table('payment_intents')
    op.drop_table('professional_prices')
    op.drop_table('pricing_policies')