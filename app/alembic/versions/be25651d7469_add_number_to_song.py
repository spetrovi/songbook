"""Add number to Song

Revision ID: be25651d7469
Revises: 762d1358d6a3
Create Date: 2024-08-01 00:10:40.098002

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "be25651d7469"
down_revision: Union[str, None] = "762d1358d6a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("song", sa.Column("number", sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("song", "number")
    # ### end Alembic commands ###