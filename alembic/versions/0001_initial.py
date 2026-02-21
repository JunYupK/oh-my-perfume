"""initial schema"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        'brands',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('fragrantica_url', sa.String(length=1024), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_brands_name'),
        sa.UniqueConstraint('slug', name='uq_brands_slug')
    )

    op.create_table(
        'perfumes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('brand_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('concentration', sa.String(length=64), nullable=False),
        sa.Column('gender', sa.String(length=32), nullable=False),
        sa.Column('fragrantica_url', sa.String(length=1024), nullable=False),
        sa.Column('last_crawled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('brand_id', 'slug', name='uq_perfumes_brand_slug')
    )

    op.create_table(
        'perfume_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('perfume_id', sa.Integer(), nullable=False),
        sa.Column('note_name', sa.String(length=255), nullable=False),
        sa.Column('note_type', sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(['perfume_id'], ['perfumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'perfume_accords',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('perfume_id', sa.Integer(), nullable=False),
        sa.Column('accord_name', sa.String(length=255), nullable=False),
        sa.Column('strength', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['perfume_id'], ['perfumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'perfume_embeddings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('perfume_id', sa.Integer(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['perfume_id'], ['perfumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('perfume_id', name='uq_perfume_embeddings_perfume_id')
    )

    op.create_table(
        'crawl_state_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_key', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('total_pages', sa.Integer(), nullable=True),
        sa.Column('processed_pages', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index("ix_brands_slug", "brands", ["slug"])
    op.create_index("ix_perfumes_brand_id", "perfumes", ["brand_id"])
    op.create_index("ix_perfumes_last_crawled_at", "perfumes", ["last_crawled_at"])
    op.create_index("ix_perfume_notes_perfume_id", "perfume_notes", ["perfume_id"])
    op.create_index("ix_perfume_accords_perfume_id", "perfume_accords", ["perfume_id"])
    op.create_index("ix_perfume_embeddings_perfume_id", "perfume_embeddings", ["perfume_id"])
    op.create_index("ix_crawl_state_log_session_key", "crawl_state_log", ["session_key"])

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_perfume_embeddings_vector_hnsw "
        "ON perfume_embeddings USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_perfume_embeddings_vector_hnsw")
    op.drop_index("ix_crawl_state_log_session_key", table_name="crawl_state_log")
    op.drop_index("ix_perfume_embeddings_perfume_id", table_name="perfume_embeddings")
    op.drop_index("ix_perfume_accords_perfume_id", table_name="perfume_accords")
    op.drop_index("ix_perfume_notes_perfume_id", table_name="perfume_notes")
    op.drop_index("ix_perfumes_last_crawled_at", table_name="perfumes")
    op.drop_index("ix_perfumes_brand_id", table_name="perfumes")
    op.drop_index("ix_brands_slug", table_name="brands")
    op.drop_table('crawl_state_log')
    op.drop_table('perfume_embeddings')
    op.drop_table('perfume_accords')
    op.drop_table('perfume_notes')
    op.drop_table('perfumes')
    op.drop_table('brands')
    op.execute('DROP EXTENSION IF EXISTS vector')
