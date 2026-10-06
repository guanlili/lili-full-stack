"""Add background jobs.

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op
from sqlalchemy import DateTime

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "job",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_type", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.Column("created_at", DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_job_task_type"), "job", ["task_type"])
    op.create_index(op.f("ix_job_status"), "job", ["status"])
    op.create_index(op.f("ix_job_owner_user_id"), "job", ["owner_user_id"])


def downgrade():
    op.drop_index(op.f("ix_job_owner_user_id"), table_name="job")
    op.drop_index(op.f("ix_job_status"), table_name="job")
    op.drop_index(op.f("ix_job_task_type"), table_name="job")
    op.drop_table("job")
