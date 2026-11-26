"""add refresh_token user_id foreign key with cascade delete

Revision ID: 0008
Revises: 0007

RefreshToken.user_id 补数据库外键并 ON DELETE CASCADE：删号时其刷新令牌随用户一并
清理，作为应用层 delete_user_refresh_tokens 的双保险。审计日志刻意保留裸引用，不在此列。
"""

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.create_foreign_key(
        "fk_refresh_token_user_id",
        "refresh_token",
        "user",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint("fk_refresh_token_user_id", "refresh_token", type_="foreignkey")
