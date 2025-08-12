"""add_ib_integration_tables

Revision ID: 2859429a2804
Revises: 0db58ed17452
Create Date: 2025-08-11 19:52:34.992199

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2859429a2804'
down_revision: Union[str, None] = '0db58ed17452'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
