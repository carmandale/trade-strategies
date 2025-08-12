"""add_ib_integration_tables

Revision ID: 2859429a2804
Revises: 0db58ed17452
Create Date: 2025-08-11 19:52:34.992199

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '2859429a2804'
down_revision: Union[str, None] = '0db58ed17452'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	# Create ib_settings table
	op.create_table('ib_settings',
		sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
		sa.Column('user_id', sa.Integer(), nullable=True),
		sa.Column('host', sa.String(length=255), server_default='127.0.0.1', nullable=True),
		sa.Column('port', sa.Integer(), server_default='7497', nullable=True),
		sa.Column('client_id', sa.Integer(), server_default='1', nullable=True),
		sa.Column('account', sa.String(length=50), nullable=True),
		sa.Column('market_data_type', sa.Integer(), server_default='1', nullable=True),
		sa.Column('auto_connect', sa.Boolean(), server_default='false', nullable=True),
		sa.Column('encrypted_credentials', sa.Text(), nullable=True),
		sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
		sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
		sa.PrimaryKeyConstraint('id')
	)
	op.create_index('idx_ib_settings_user', 'ib_settings', ['user_id'], unique=False)
	
	# Create options_data_cache table
	op.create_table('options_data_cache',
		sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
		sa.Column('symbol', sa.String(length=10), nullable=False),
		sa.Column('strike', sa.DECIMAL(precision=10, scale=2), nullable=False),
		sa.Column('expiration', sa.DateTime(), nullable=False),
		sa.Column('option_type', sa.String(length=4), nullable=False),
		sa.Column('bid', sa.DECIMAL(precision=10, scale=2), nullable=True),
		sa.Column('ask', sa.DECIMAL(precision=10, scale=2), nullable=True),
		sa.Column('last', sa.DECIMAL(precision=10, scale=2), nullable=True),
		sa.Column('volume', sa.Integer(), nullable=True),
		sa.Column('open_interest', sa.Integer(), nullable=True),
		sa.Column('implied_volatility', sa.DECIMAL(precision=6, scale=4), nullable=True),
		sa.Column('delta', sa.DECIMAL(precision=6, scale=4), nullable=True),
		sa.Column('gamma', sa.DECIMAL(precision=8, scale=6), nullable=True),
		sa.Column('theta', sa.DECIMAL(precision=8, scale=2), nullable=True),
		sa.Column('vega', sa.DECIMAL(precision=8, scale=2), nullable=True),
		sa.Column('rho', sa.DECIMAL(precision=8, scale=2), nullable=True),
		sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
		sa.Column('ttl_seconds', sa.Integer(), server_default='5', nullable=True),
		sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
		sa.CheckConstraint("option_type IN ('call', 'put')", name='check_option_type'),
		sa.PrimaryKeyConstraint('id'),
		sa.UniqueConstraint('symbol', 'strike', 'expiration', 'option_type', 'timestamp')
	)
	op.create_index('idx_options_cache_symbol', 'options_data_cache', ['symbol', 'expiration'], unique=False)
	op.create_index('idx_options_cache_timestamp', 'options_data_cache', ['timestamp'], unique=False)
	
	# Create historical_options_data table
	op.create_table('historical_options_data',
		sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
		sa.Column('symbol', sa.String(length=10), nullable=False),
		sa.Column('strike', sa.DECIMAL(precision=10, scale=2), nullable=False),
		sa.Column('expiration', sa.DateTime(), nullable=False),
		sa.Column('option_type', sa.String(length=4), nullable=False),
		sa.Column('date', sa.DateTime(), nullable=False),
		sa.Column('open', sa.DECIMAL(precision=10, scale=2), nullable=True),
		sa.Column('high', sa.DECIMAL(precision=10, scale=2), nullable=True),
		sa.Column('low', sa.DECIMAL(precision=10, scale=2), nullable=True),
		sa.Column('close', sa.DECIMAL(precision=10, scale=2), nullable=True),
		sa.Column('volume', sa.Integer(), nullable=True),
		sa.Column('open_interest', sa.Integer(), nullable=True),
		sa.Column('implied_volatility', sa.DECIMAL(precision=6, scale=4), nullable=True),
		sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
		sa.CheckConstraint("option_type IN ('call', 'put')", name='check_hist_option_type'),
		sa.PrimaryKeyConstraint('id'),
		sa.UniqueConstraint('symbol', 'strike', 'expiration', 'option_type', 'date')
	)
	op.create_index('idx_historical_options_symbol', 'historical_options_data', ['symbol', 'date'], unique=False)
	op.create_index('idx_historical_options_range', 'historical_options_data', ['symbol', 'date', 'strike'], unique=False)
	
	# Create ib_connection_log table
	op.create_table('ib_connection_log',
		sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
		sa.Column('event_type', sa.String(length=50), nullable=False),
		sa.Column('status', sa.String(length=20), nullable=False),
		sa.Column('account', sa.String(length=50), nullable=True),
		sa.Column('error_message', sa.Text(), nullable=True),
		sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
		sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
		sa.PrimaryKeyConstraint('id')
	)
	op.create_index('idx_ib_log_created', 'ib_connection_log', ['created_at'], unique=False)
	op.create_index('idx_ib_log_event', 'ib_connection_log', ['event_type'], unique=False)
	
	# Add columns to strategies table
	op.add_column('strategies', sa.Column('data_source', sa.String(length=20), server_default='estimated', nullable=True))
	op.add_column('strategies', sa.Column('ib_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
	# Remove columns from strategies table
	op.drop_column('strategies', 'ib_snapshot')
	op.drop_column('strategies', 'data_source')
	
	# Drop tables in reverse order
	op.drop_index('idx_ib_log_event', table_name='ib_connection_log')
	op.drop_index('idx_ib_log_created', table_name='ib_connection_log')
	op.drop_table('ib_connection_log')
	
	op.drop_index('idx_historical_options_range', table_name='historical_options_data')
	op.drop_index('idx_historical_options_symbol', table_name='historical_options_data')
	op.drop_table('historical_options_data')
	
	op.drop_index('idx_options_cache_timestamp', table_name='options_data_cache')
	op.drop_index('idx_options_cache_symbol', table_name='options_data_cache')
	op.drop_table('options_data_cache')
	
	op.drop_index('idx_ib_settings_user', table_name='ib_settings')
	op.drop_table('ib_settings')