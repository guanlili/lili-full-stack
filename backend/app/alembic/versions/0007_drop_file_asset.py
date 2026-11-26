"""drop file_asset skeleton table

Revision ID: 0007
Revises: 32f63b6790af

上传骨架（FileAsset 模型 / 上传路由 / 落盘卷）未接线，先从模板剥离；
需要文件上传能力时再按带 MIME 白名单、大小校验与 owner 隔离的样板加回。
system_setting 表不在本次剥离范围。
"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op
from sqlalchemy import DateTime

revision = "0007"
down_revision = "32f63b6790af"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index(op.f("ix_file_asset_owner_user_id"), table_name="file_asset")
    op.drop_index(
        op.f("ix_file_asset_stored_name"), table_name="file_asset"
    )
    op.drop_table("file_asset")


def downgrade():
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
    op.create_index(
        op.f("ix_file_asset_stored_name"),
        "file_asset",
        ["stored_name"],
        unique=True,
    )
    op.create_index(
        op.f("ix_file_asset_owner_user_id"),
        "file_asset",
        ["owner_user_id"],
    )
