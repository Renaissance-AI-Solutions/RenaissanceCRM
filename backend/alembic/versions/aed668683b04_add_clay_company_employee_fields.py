"""add clay company employee fields

Revision ID: aed668683b04
Revises: b7406ad17ed5
Create Date: 2026-02-16 02:25:38.045198
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'aed668683b04'
down_revision: Union[str, None] = 'b7406ad17ed5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define the enum so we can create/drop it explicitly
enrichment_status_enum = sa.Enum(
    'NOT_NEEDED', 'PENDING', 'QUEUED', 'ENRICHED', 'FAILED',
    name='enrichmentstatus',
)


def upgrade() -> None:
    # Create the enum type first
    enrichment_status_enum.create(op.get_bind(), checkfirst=True)

    # Companies — new Clay fields
    op.add_column('companies', sa.Column('google_maps_url', sa.String(length=500), nullable=True))
    op.add_column('companies', sa.Column('rating', sa.Float(), nullable=True))
    op.add_column('companies', sa.Column('reviews_count', sa.Integer(), nullable=True))

    # Contacts — new Clay employee fields
    op.add_column('contacts', sa.Column('linkedin_url', sa.String(length=500), nullable=True))
    op.add_column('contacts', sa.Column('departments', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False))
    op.add_column('contacts', sa.Column('seniorities', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False))
    op.add_column('contacts', sa.Column('is_primary_contact', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('contacts', sa.Column('enrichment_status', enrichment_status_enum, nullable=True))
    op.add_column('contacts', sa.Column('personal_emails', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False))


def downgrade() -> None:
    op.drop_column('contacts', 'personal_emails')
    op.drop_column('contacts', 'enrichment_status')
    op.drop_column('contacts', 'is_primary_contact')
    op.drop_column('contacts', 'seniorities')
    op.drop_column('contacts', 'departments')
    op.drop_column('contacts', 'linkedin_url')
    op.drop_column('companies', 'reviews_count')
    op.drop_column('companies', 'rating')
    op.drop_column('companies', 'google_maps_url')

    # Drop the enum type
    enrichment_status_enum.drop(op.get_bind(), checkfirst=True)
