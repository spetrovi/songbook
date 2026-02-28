"""Add source-author many-to-many and transcribed_by string

Revision ID: 0ab4957ec7d6
Revises: 8cec5da81761
Create Date: 2026-02-28 19:36:28.571828

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
import sqlmodel
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0ab4957ec7d6"
down_revision: Union[str, None] = "8cec5da81761"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create many-to-many link table for Source <-> Person
    op.create_table(
        "sourceauthorlink",
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["source.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("source_id", "person_id"),
    )

    # 2. Copy existing author_id data into link table (optional, safe even if empty)
    op.execute(
        """
        INSERT INTO sourceauthorlink (source_id, person_id)
        SELECT id, author_id
        FROM source
        WHERE author_id IS NOT NULL
        """
    )

    # 3. Add transcribed_by columns
    op.add_column(
        "song",
        sa.Column("transcribed_by", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    op.add_column(
        "source",
        sa.Column("transcribed_by", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )

    # 4. Drop old author_id foreign key and column
    op.drop_constraint(op.f("source_author_id_fkey"), "source", type_="foreignkey")
    op.drop_column("source", "author_id")


def downgrade() -> None:
    # 1. Re-add old author_id column
    op.add_column(
        "source", sa.Column("author_id", sa.UUID(), autoincrement=False, nullable=True)
    )
    op.create_foreign_key(
        op.f("source_author_id_fkey"), "source", "person", ["author_id"], ["id"]
    )

    # 2. Remove transcribed_by columns
    op.drop_column("source", "transcribed_by")
    op.drop_column("song", "transcribed_by")

    # 3. Drop many-to-many link table
    op.drop_table("sourceauthorlink")
