"""Initial database schema with users, strategies, backtests, and trades tables

Revision ID: 2aefcf550525
Revises: 
Create Date: 2025-07-30 11:49:45.306192

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2aefcf550525'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
