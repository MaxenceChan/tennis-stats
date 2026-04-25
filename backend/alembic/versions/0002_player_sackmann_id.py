"""add sackmann_id and wikidata_id to players

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-25
"""
from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("players") as batch:
        batch.add_column(sa.Column("sackmann_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("wikidata_id", sa.String(40), nullable=True))
        batch.create_index("ix_players_sackmann_id", ["sackmann_id"])


def downgrade() -> None:
    with op.batch_alter_table("players") as batch:
        batch.drop_index("ix_players_sackmann_id")
        batch.drop_column("wikidata_id")
        batch.drop_column("sackmann_id")
