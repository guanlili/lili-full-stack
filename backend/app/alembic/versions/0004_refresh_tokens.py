"""Add rotating refresh tokens.

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op
from sqlalchemy import DateTime

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "refresh_token",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "token_hash", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False
        ),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("expires_at", DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", DateTime(timezone=True), nullable=True),
        sa.Column("created_at", DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_refresh_token_token_hash"), "refresh_token", ["token_hash"], unique=True)
    op.create_index(op.f("ix_refresh_token_user_id"), "refresh_token", ["user_id"])


def downgrade():
    op.drop_index(op.f("ix_refresh_token_user_id"), table_name="refresh_token")
    op.drop_index(op.f("ix_refresh_token_token_hash"), table_name="refresh_token")
    op.drop_table("refresh_token")
