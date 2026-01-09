"""add composite index on hall_id and date

Revision ID: 148eac57d8e3
Revises: 3a941c7c34a2
Create Date: 2026-01-09 18:50:45.134900

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '148eac57d8e3'
down_revision = '3a941c7c34a2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('booking', schema=None) as batch_op:
        batch_op.create_index('ix_booking_hall_id_date', ['hall_id', 'date'], unique=False)


def downgrade():
    with op.batch_alter_table('booking', schema=None) as batch_op:
        batch_op.drop_index('ix_booking_hall_id_date')
