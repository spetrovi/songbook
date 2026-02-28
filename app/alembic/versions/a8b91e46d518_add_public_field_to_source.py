"""add public field to source

Revision ID: a8b91e46d518
Revises: 0ab4957ec7d6
Create Date: 2026-02-28 21:18:03.185041

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a8b91e46d518"
down_revision: Union[str, None] = "0ab4957ec7d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "source",
        sa.Column(
            "public",
            sa.Boolean(),
            nullable=False,
            server_default=sa.sql.expression.false(),
        ),
    )


def downgrade() -> None:
    op.alter_column("source", "public", server_default=None)
