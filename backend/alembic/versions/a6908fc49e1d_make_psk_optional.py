"""make_psk_optional

Revision ID: a6908fc49e1d
Revises: cc2e0f4b0d3a
Create Date: 2026-01-31 16:18:29.128817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6908fc49e1d'
down_revision: Union[str, Sequence[str], None] = 'cc2e0f4b0d3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('displays', schema=None) as batch_op:
        batch_op.alter_column('psk',
                              existing_type=sa.String(255),
                              nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('displays', schema=None) as batch_op:
        batch_op.alter_column('psk',
                              existing_type=sa.String(255),
                              nullable=False)
