"""add draft_emails table

Revision ID: c3f891d24a17
Revises: aed668683b04
Create Date: 2026-02-16 13:01:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3f891d24a17'
down_revision: Union[str, None] = 'aed668683b04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type safely using DO block (idempotent)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'draftemailstatus') THEN
                CREATE TYPE draftemailstatus AS ENUM ('DRAFT', 'APPROVED', 'SENT', 'REJECTED');
            END IF;
        END
        $$;
    """)

    # Use create_type=False so SQLAlchemy does NOT auto-emit CREATE TYPE
    status_col = postgresql.ENUM(
        'DRAFT', 'APPROVED', 'SENT', 'REJECTED',
        name='draftemailstatus',
        create_type=False,
    )

    op.create_table(
        'draft_emails',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('contacts.id'), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('status', status_col, nullable=False, server_default='DRAFT'),
        sa.Column('ai_model', sa.String(length=100), nullable=True),
        sa.Column('ai_reasoning', sa.Text(), nullable=True),
        sa.Column('website_snapshot', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_index('ix_draft_emails_tenant', 'draft_emails', ['tenant_id'])
    op.create_index('ix_draft_emails_company', 'draft_emails', ['company_id'])
    op.create_index('ix_draft_emails_contact', 'draft_emails', ['contact_id'])
    op.create_index('ix_draft_emails_status', 'draft_emails', ['status'])


def downgrade() -> None:
    op.drop_index('ix_draft_emails_status', table_name='draft_emails')
    op.drop_index('ix_draft_emails_contact', table_name='draft_emails')
    op.drop_index('ix_draft_emails_company', table_name='draft_emails')
    op.drop_index('ix_draft_emails_tenant', table_name='draft_emails')
    op.drop_table('draft_emails')
    op.execute('DROP TYPE IF EXISTS draftemailstatus')
