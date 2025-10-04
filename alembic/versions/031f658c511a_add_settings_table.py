"""Add settings table

Revision ID: 031f658c511a
Revises: ef6345c09746
Create Date: 2025-10-01 20:14:29.569761

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '031f658c511a'
down_revision = 'ef6345c09746'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create table settings for system configuration."""
    op.create_table(
        'settings',
        sa.Column('key', sa.String(length=100), primary_key=True, nullable=False, comment='Ключ настройки'),
        sa.Column('value', sa.Text(), nullable=False, comment='Значение настройки'),
        sa.Column('value_type', sa.String(length=20), nullable=False, comment='Тип значения: int, float, string, bool'),
        sa.Column('category', sa.String(length=50), nullable=False, comment='Категория: financial, pricing, alerts, ai, operational'),
        sa.Column('description', sa.Text(), nullable=True, comment='Описание настройки'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True, comment='Время последнего обновления'),
        sa.Column('updated_by', sa.String(length=50), nullable=True, server_default='system', comment='Кто обновил')
    )
    op.create_index('ix_settings_category', 'settings', ['category'])


def downgrade() -> None:
    """Drop settings table."""
    op.drop_index('ix_settings_category', table_name='settings')
    op.drop_table('settings')
