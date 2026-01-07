'''alembic revision --autogenerate -m "add cache_entry and search_history tables"'''

"""Add CacheEntry and SearchHistory tables"""

from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision = '20260107_add_cache_history'
down_revision = None  # set appropriate down revision if needed
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'cache_entry',
        sa.Column('id', sa.String(length=36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('key', sa.String(length=512), nullable=False, unique=True, index=True),
        sa.Column('result_json', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        'search_history',
        sa.Column('id', sa.String(length=36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('key', sa.String(length=512), nullable=False, index=True),
        sa.Column('url', sa.String(length=1024), nullable=True),
        sa.Column('result_summary', sa.String(length=1024), nullable=True),
        sa.Column('source', sa.String(length=16), nullable=False, server_default='remote'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table('search_history')
    op.drop_table('cache_entry')
