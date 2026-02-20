"""Add ingest tables

Revision ID: 3b9d4df6c2a1
Revises: 1a9c0d2b9c53
Create Date: 2026-02-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "3b9d4df6c2a1"
down_revision: Union[str, None] = "1a9c0d2b9c53"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "category",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("foursquare_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("icon_prefix", sa.String(), nullable=True),
        sa.Column("icon_suffix", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("foursquare_id"),
    )

    op.create_table(
        "chain",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("foursquare_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("foursquare_id"),
    )

    op.create_table(
        "pointofinterest",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("foursquare_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("state", sa.String(), nullable=True),
        sa.Column("zip_code", sa.String(), nullable=True),
        sa.Column("popularity", sa.Float(), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("price", sa.Integer(), nullable=True),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("social_media", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("category_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("chain_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("foursquare_id", name="uq_pointofinterest_foursquare_id"),
    )

    op.create_index(
        "ix_pointofinterest_lat_lng",
        "pointofinterest",
        ["latitude", "longitude"],
        unique=False,
    )

    op.create_table(
        "job",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("previous_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["previous_id"], ["job.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "status", name="uq_job_source_status"),
    )

    op.create_index("ix_job_previous_id", "job", ["previous_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_job_previous_id", table_name="job")
    op.drop_table("job")
    op.drop_index("ix_pointofinterest_lat_lng", table_name="pointofinterest")
    op.drop_table("pointofinterest")
    op.drop_table("chain")
    op.drop_table("category")
