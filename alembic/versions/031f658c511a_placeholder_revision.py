"""Placeholder revision to bridge missing DB state

Revision ID: 031f658c511a
Revises: ef6345c09746
Create Date: 2025-10-04 19:40:00.000000

Этот файл создан для согласования с существующей БД DEV/TEST,
которые уже отмечены этой ревизией. Миграция не содержит действий.
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "031f658c511a"
down_revision = "ef6345c09746"
branch_labels = None
depends_on = None


def upgrade() -> None:  # pragma: no cover
    """No-op upgrade."""
    pass


def downgrade() -> None:  # pragma: no cover
    """No-op downgrade."""
    pass
