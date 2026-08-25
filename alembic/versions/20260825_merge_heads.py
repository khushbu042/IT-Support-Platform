"""Merge Alembic heads 6b70e1f043f3 and 20260825_add_userrole_values

Revision ID: 20260825_merge_heads
Revises: 6b70e1f043f3, 20260825_add_userrole_values
Create Date: 2026-08-25 00:10:00.000000

This is a merge revision to unify two concurrent heads into a single
linear history so `alembic upgrade head` can be executed.
"""
from alembic import op
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "20260825_merge_heads"
down_revision: Union[str, Sequence[str], None] = ("6b70e1f043f3", "20260825_add_userrole_values")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This merge revision has no schema operations; it only resolves multiple
    # heads by recording a single downstream revision that depends on both.
    pass


def downgrade() -> None:
    # Downgrade would re-create the divergent heads — handle manually if needed.
    pass
