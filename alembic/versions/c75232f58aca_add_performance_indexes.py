"""add performance indexes

Revision ID: c75232f58aca
Revises: 257ad6689ecd
Create Date: 2026-01-27 21:41:35.545013

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c75232f58aca'
down_revision: Union[str, Sequence[str], None] = '257ad6689ecd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
