"""Add column description to Songbook model

Revision ID: 1f7d5d0ff95b
Revises: 0c6a72ee71c2
Create Date: 2024-05-02 19:04:46.589912

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
import sqlmodel
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "1f7d5d0ff95b"
down_revision: Union[str, None] = "0c6a72ee71c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "songbook",
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("songbook", "description")
    # ### end Alembic commands ###
