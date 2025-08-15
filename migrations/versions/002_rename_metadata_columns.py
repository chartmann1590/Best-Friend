"""Rename metadata columns to avoid SQLAlchemy conflicts

Revision ID: 002
Revises: 001
Create Date: 2024-08-15 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename metadata column in messages table to message_metadata
    op.alter_column('messages', 'metadata', new_column_name='message_metadata')
    
    # Rename metadata column in memories table to memory_metadata
    op.alter_column('memories', 'metadata', new_column_name='memory_metadata')


def downgrade() -> None:
    # Revert message_metadata back to metadata
    op.alter_column('messages', 'message_metadata', new_column_name='metadata')
    
    # Revert memory_metadata back to metadata
    op.alter_column('memories', 'memory_metadata', new_column_name='metadata')
