"""Add file assets and system settings.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op
from sqlalchemy import DateTime

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "file_asset",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "original_name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False
        ),
        sa.Column(
            "stored_name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False
        ),
        sa.Column(
            "content_type", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True
        ),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_file_asset_stored_name"), "file_asset", ["stored_name"], unique=True)
    op.create_index(op.f("ix_file_asset_owner_user_id"), "file_asset", ["owner_user_id"])

    op.create_table(
        "system_setting",
        sa.Column("key", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("value", sqlmodel.sql.sqltypes.AutoString(length=4000), nullable=False),
        sa.Column(
            "description", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True
        ),
        sa.Column("updated_at", DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade():
    op.drop_table("system_setting")
    op.drop_index(op.f("ix_file_asset_owner_user_id"), table_name="file_asset")
    op.drop_index(op.f("ix_file_asset_stored_name"), table_name="file_asset")
    op.drop_table("file_asset")
