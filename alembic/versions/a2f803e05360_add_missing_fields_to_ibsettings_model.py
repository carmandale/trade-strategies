"""Add missing fields to IBSettings model

Revision ID: a2f803e05360
Revises: 2859429a2804
Create Date: 2025-08-12 10:28:49.599547

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a2f803e05360'
down_revision: Union[str, None] = '2859429a2804'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing fields to ib_settings table
    op.add_column('ib_settings', sa.Column('active', sa.Boolean(), server_default='true', nullable=True))
    op.add_column('ib_settings', sa.Column('connection_timeout', sa.Integer(), server_default='10', nullable=True))
    op.add_column('ib_settings', sa.Column('retry_attempts', sa.Integer(), server_default='3', nullable=True))
    op.add_column('ib_settings', sa.Column('market_data_permissions', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    # Remove added fields
    op.drop_column('ib_settings', 'market_data_permissions')
    op.drop_column('ib_settings', 'retry_attempts')
    op.drop_column('ib_settings', 'connection_timeout')
    op.drop_column('ib_settings', 'active')
