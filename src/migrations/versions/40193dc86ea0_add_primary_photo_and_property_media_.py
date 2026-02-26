"""add primary_photo and property_media table

Revision ID: 40193dc86ea0
Revises: 3b9d4df6c2a1
Create Date: 2026-02-26 15:02:14.934882

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40193dc86ea0'
down_revision: Union[str, None] = '3b9d4df6c2a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('property_media',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('property_id', sa.String(), nullable=False),
    sa.Column('s3_path', sa.String(), nullable=False),
    sa.Column('kind', sa.String(), nullable=False),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['property_id'], ['public.property.listing_key'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='public'
    )
    op.add_column('property', sa.Column('primary_photo', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('property', 'primary_photo')
    op.drop_table('property_media', schema='public')
