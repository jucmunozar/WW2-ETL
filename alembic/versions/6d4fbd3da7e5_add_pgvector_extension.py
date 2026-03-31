"""add_pgvector_extension

Revision ID: 6d4fbd3da7e5
Revises: 1af69acd6ac7
Create Date: 2026-03-30 09:18:58.624897

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6d4fbd3da7e5'
down_revision: Union[str, Sequence[str], None] = '1af69acd6ac7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP EXTENSION IF EXISTS vector;")
