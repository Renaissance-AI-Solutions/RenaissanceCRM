"""add email_threads table and thread linking columns

Revision ID: d7e4f891ab23
Revises: c3f891d24a17
Create Date: 2026-03-01 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'd7e4f891ab23'
down_revision: Union[str, None] = 'c3f891d24a17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create emailthreadstatus enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'emailthreadstatus') THEN
                CREATE TYPE emailthreadstatus AS ENUM ('active', 'closed');
            END IF;
        END
        $$;
    """)

    thread_status_col = postgresql.ENUM(
        'active', 'closed',
        name='emailthreadstatus',
        create_type=False,
    )

    # Create email_threads table
    op.create_table(
        'email_threads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('contacts.id'), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('gmail_thread_id', sa.String(length=255), nullable=True),
        sa.Column('status', thread_status_col, nullable=False, server_default='active'),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_email_threads_tenant', 'email_threads', ['tenant_id'])
    op.create_index('ix_email_threads_contact', 'email_threads', ['contact_id'])
    op.create_index('ix_email_threads_status', 'email_threads', ['status'])

    # Add thread_id + gmail_message_id to draft_emails
    op.add_column('draft_emails', sa.Column('thread_id', postgresql.UUID(as_uuid=True),
        sa.ForeignKey('email_threads.id'), nullable=True))
    op.add_column('draft_emails', sa.Column('gmail_message_id', sa.String(length=255), nullable=True))
    op.create_index('ix_draft_emails_thread', 'draft_emails', ['thread_id'])

    # Add thread_id + gmail_message_id to activities
    op.add_column('activities', sa.Column('thread_id', postgresql.UUID(as_uuid=True),
        sa.ForeignKey('email_threads.id'), nullable=True))
    op.add_column('activities', sa.Column('gmail_message_id', sa.String(length=255), nullable=True))
    op.create_index('ix_activities_thread', 'activities', ['thread_id'])


def downgrade() -> None:
    op.drop_index('ix_activities_thread', table_name='activities')
    op.drop_column('activities', 'gmail_message_id')
    op.drop_column('activities', 'thread_id')

    op.drop_index('ix_draft_emails_thread', table_name='draft_emails')
    op.drop_column('draft_emails', 'gmail_message_id')
    op.drop_column('draft_emails', 'thread_id')

    op.drop_index('ix_email_threads_status', table_name='email_threads')
    op.drop_index('ix_email_threads_contact', table_name='email_threads')
    op.drop_index('ix_email_threads_tenant', table_name='email_threads')
    op.drop_table('email_threads')
    op.execute('DROP TYPE IF EXISTS emailthreadstatus')
