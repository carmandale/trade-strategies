"""Initial database schema with users, strategies, backtests, and trades tables

Revision ID: 2aefcf550525
Revises: 
Create Date: 2025-07-30 11:49:45.306192

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2aefcf550525'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Simplify initial revision for compatibility; later revision reshapes schema
    
    # Create users table
    op.create_table('users',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create strategies table
    op.create_table('strategies',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('strategy_type', sa.String(length=50), nullable=False),
    sa.Column('strikes', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('contracts', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create backtests table
    op.create_table('backtests',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('strategy_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('analysis_date', sa.DateTime(), nullable=False),
    sa.Column('entry_time', sa.String(length=10), nullable=False),
    sa.Column('exit_time', sa.String(length=10), nullable=False),
    sa.Column('results', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create trades table
    op.create_table('trades',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('strategy_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('execution_date', sa.DateTime(), nullable=False),
    sa.Column('entry_price', sa.DECIMAL(precision=10, scale=2), nullable=True),
    sa.Column('exit_price', sa.DECIMAL(precision=10, scale=2), nullable=True),
    sa.Column('pnl', sa.DECIMAL(precision=10, scale=2), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('contracts', sa.Integer(), nullable=False),
    sa.Column('strategy_type', sa.String(length=50), nullable=False),
    sa.Column('strikes_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('trades')
    op.drop_table('backtests')
    op.drop_table('strategies')
    op.drop_table('users')
    op.execute("DROP TYPE IF EXISTS tradestatus")
    op.execute("DROP TYPE IF EXISTS strategytype")
