"""add_clerk_user_id_to_organizations

Revision ID: 002
Revises: 001
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column("clerk_user_id", sa.String(), nullable=True),
    )
    op.create_index("ix_organizations_clerk_user_id", "organizations", ["clerk_user_id"])


def downgrade() -> None:
    op.drop_index("ix_organizations_clerk_user_id", table_name="organizations")
    op.drop_column("organizations", "clerk_user_id")
