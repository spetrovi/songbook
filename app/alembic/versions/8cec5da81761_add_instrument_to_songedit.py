"""Add instrument to songedit

Revision ID: 8cec5da81761
Revises: be25651d7469
Create Date: 2024-11-14 17:21:06.936836

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
import sqlmodel
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "8cec5da81761"
down_revision: Union[str, None] = "be25651d7469"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "songedit",
        sa.Column("instrument", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("songedit", "instrument")
    # ### end Alembic commands ###
