"""add user profile and platform identity fields

Revision ID: c4f7a91e2b6d
Revises: 7c582e4ad75e
Create Date: 2026-09-08 12:05:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4f7a91e2b6d"
down_revision: Union[str, Sequence[str], None] = "7c582e4ad75e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add permanent user identity and profile fields safely."""

    # Existing accounts are already present, so the columns must first
    # be introduced as nullable and populated before NOT NULL is enforced.
    op.add_column(
        "users",
        sa.Column(
            "user_id",
            sa.String(length=20),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "first_name",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "last_name",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "mobile_number",
            sa.String(length=20),
            nullable=True,
        ),
    )

    # Backfill existing accounts with deterministic platform IDs and
    # unique migration-only mobile placeholders. New registrations will
    # require real first name, last name and mobile number values.
    op.execute(
        sa.text(
            """
            WITH numbered_users AS (
                SELECT
                    id,
                    ROW_NUMBER() OVER (ORDER BY id) AS row_number
                FROM users
            )
            UPDATE users AS u
            SET
                user_id = 'USR-' ||
                    SUBSTRING(REPLACE(u.id::text, '-', '') FROM 1 FOR 12),
                first_name = 'Account',
                last_name = 'User',
                mobile_number =
                    (9000000000 + numbered_users.row_number - 1)::text
            FROM numbered_users
            WHERE u.id = numbered_users.id
            """
        )
    )

    op.alter_column(
        "users",
        "user_id",
        existing_type=sa.String(length=20),
        nullable=False,
    )

    op.alter_column(
        "users",
        "first_name",
        existing_type=sa.String(length=100),
        nullable=False,
    )

    op.alter_column(
        "users",
        "last_name",
        existing_type=sa.String(length=100),
        nullable=False,
    )

    op.alter_column(
        "users",
        "mobile_number",
        existing_type=sa.String(length=20),
        nullable=False,
    )

    op.create_index(
        "ix_users_user_id",
        "users",
        ["user_id"],
        unique=True,
    )

    op.create_index(
        "ix_users_mobile_number",
        "users",
        ["mobile_number"],
        unique=True,
    )


def downgrade() -> None:
    """Remove the user profile and platform identity fields."""

    op.drop_index(
        "ix_users_mobile_number",
        table_name="users",
    )

    op.drop_index(
        "ix_users_user_id",
        table_name="users",
    )

    op.drop_column(
        "users",
        "mobile_number",
    )

    op.drop_column(
        "users",
        "last_name",
    )

    op.drop_column(
        "users",
        "first_name",
    )

    op.drop_column(
        "users",
        "user_id",
    )
