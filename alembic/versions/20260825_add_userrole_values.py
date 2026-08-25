"""Add userrole enum values: customer, agent, admin

Revision ID: 20260825_add_userrole_values
Revises: d8d03da164d3
Create Date: 2026-08-25 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260825_add_userrole_values"
down_revision = "d8d03da164d3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing enum labels if they do not already exist.
    op.execute(
        """
    DO $$
    BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_enum WHERE enumlabel = 'customer' AND enumtypid = 'userrole'::regtype
      ) THEN
        ALTER TYPE userrole ADD VALUE 'customer';
      END IF;

      IF NOT EXISTS (
        SELECT 1 FROM pg_enum WHERE enumlabel = 'agent' AND enumtypid = 'userrole'::regtype
      ) THEN
        ALTER TYPE userrole ADD VALUE 'agent';
      END IF;

      IF NOT EXISTS (
        SELECT 1 FROM pg_enum WHERE enumlabel = 'admin' AND enumtypid = 'userrole'::regtype
      ) THEN
        ALTER TYPE userrole ADD VALUE 'admin';
      END IF;
    END$$;
    """
    )


def downgrade() -> None:
    # Removing enum labels is non-trivial in PostgreSQL and may require creating
    # a new type and casting columns. This downgrade is intentionally left
    # empty; reverse migration should be performed manually if needed.
    pass
