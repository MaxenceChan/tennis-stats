"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-25
"""
from alembic import op
import sqlalchemy as sa


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("first_name", sa.String(80)),
        sa.Column("last_name", sa.String(80)),
        sa.Column("full_name", sa.String(160), nullable=False),
        sa.Column("country", sa.String(3)),
        sa.Column("birth_date", sa.Date()),
        sa.Column("height_cm", sa.Integer()),
        sa.Column("weight_kg", sa.Integer()),
        sa.Column("hand", sa.String(1)),
        sa.Column("backhand", sa.String(1)),
        sa.Column("atp_rank", sa.Integer()),
        sa.Column("atp_points", sa.Integer()),
        sa.Column("race_rank", sa.Integer()),
        sa.Column("race_points", sa.Integer()),
        sa.Column("elo_rating", sa.Float()),
        sa.Column("wikipedia_url", sa.String(400)),
        sa.Column("tennis_abstract_url", sa.String(400)),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("slug", name="uq_players_slug"),
    )
    op.create_index("ix_players_slug", "players", ["slug"])
    op.create_index("ix_players_full_name", "players", ["full_name"])
    op.create_index("ix_players_atp_rank", "players", ["atp_rank"])
    op.create_index("ix_players_race_rank", "players", ["race_rank"])
    op.create_index("ix_players_elo_rating", "players", ["elo_rating"])

    op.create_table(
        "tournaments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(140), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("surface", sa.String(20)),
        sa.Column("category", sa.String(20)),
        sa.Column("city", sa.String(80)),
        sa.Column("country", sa.String(80)),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("draw_size", sa.Integer()),
        sa.Column("prize_money", sa.String(40)),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("slug", "year", name="uq_tournament_slug_year"),
    )
    op.create_index("ix_tournaments_slug", "tournaments", ["slug"])
    op.create_index("ix_tournaments_name", "tournaments", ["name"])
    op.create_index("ix_tournaments_year", "tournaments", ["year"])
    op.create_index("ix_tournaments_category", "tournaments", ["category"])
    op.create_index("ix_tournaments_start_date", "tournaments", ["start_date"])

    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tournament_id", sa.Integer(), sa.ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("round", sa.String(10)),
        sa.Column("match_date", sa.Date()),
        sa.Column("player1_id", sa.Integer(), sa.ForeignKey("players.id", ondelete="CASCADE"), nullable=False),
        sa.Column("player2_id", sa.Integer(), sa.ForeignKey("players.id", ondelete="CASCADE"), nullable=False),
        sa.Column("winner_id", sa.Integer(), sa.ForeignKey("players.id", ondelete="SET NULL")),
        sa.Column("loser_id", sa.Integer(), sa.ForeignKey("players.id", ondelete="SET NULL")),
        sa.Column("score", sa.String(80)),
        sa.Column("sets_count", sa.Integer()),
        sa.Column("duration_minutes", sa.Integer()),
        sa.Column("atp_rank_p1", sa.Integer()),
        sa.Column("atp_rank_p2", sa.Integer()),
        sa.Column("first_serve_pct_p1", sa.Float()),
        sa.Column("first_serve_pct_p2", sa.Float()),
        sa.Column("first_serve_win_pct_p1", sa.Float()),
        sa.Column("first_serve_win_pct_p2", sa.Float()),
        sa.Column("second_serve_win_pct_p1", sa.Float()),
        sa.Column("second_serve_win_pct_p2", sa.Float()),
        sa.Column("break_points_saved_p1", sa.Float()),
        sa.Column("break_points_saved_p2", sa.Float()),
        sa.Column("double_fault_pct_p1", sa.Float()),
        sa.Column("double_fault_pct_p2", sa.Float()),
        sa.Column("dominance_ratio_p1", sa.Float()),
        sa.Column("dominance_ratio_p2", sa.Float()),
        sa.Column("ace_pct_p1", sa.Float()),
        sa.Column("ace_pct_p2", sa.Float()),
        sa.Column("source_url", sa.String(400)),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tournament_id", "round", "player1_id", "player2_id", name="uq_match"),
    )
    op.create_index("ix_match_date", "matches", ["match_date"])
    op.create_index("ix_matches_tournament_id", "matches", ["tournament_id"])
    op.create_index("ix_matches_player1_id", "matches", ["player1_id"])
    op.create_index("ix_matches_player2_id", "matches", ["player2_id"])

    op.create_table(
        "elo_ratings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id", ondelete="CASCADE"), nullable=False),
        sa.Column("surface", sa.String(20), nullable=False, server_default="all"),
        sa.Column("rating", sa.Float(), nullable=False, server_default="1500"),
        sa.Column("matches_played", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("player_id", "surface", name="uq_elo_player_surface"),
    )
    op.create_index("ix_elo_ratings_player_id", "elo_ratings", ["player_id"])
    op.create_index("ix_elo_ratings_surface", "elo_ratings", ["surface"])


def downgrade() -> None:
    op.drop_table("elo_ratings")
    op.drop_table("matches")
    op.drop_table("tournaments")
    op.drop_table("players")
