"""add bdl_id to players

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-25
"""
from alembic import op
import sqlalchemy as sa


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("players") as batch:
        batch.add_column(sa.Column("bdl_id", sa.Integer(), nullable=True))
        batch.create_index("ix_players_bdl_id", ["bdl_id"])


def downgrade() -> None:
    with op.batch_alter_table("players") as batch:
        batch.drop_index("ix_players_bdl_id")
        batch.drop_column("bdl_id")
