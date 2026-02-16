"""add_b2c2b_models

Revision ID: 1f88001b814e
Revises: 4a69a2a5e8f8
Create Date: 2026-02-15 20:55:14.703518

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f88001b814e'
down_revision: Union[str, Sequence[str], None] = '4a69a2a5e8f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create payment_requests table
    op.create_table('payment_requests',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('merchant_id', sa.String(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True,
    )
    op.create_index(op.f('ix_payment_requests_merchant_id'), 'payment_requests', ['merchant_id'], unique=False, if_not_exists=True)

    # Modify ledger table — batch mode for SQLite
    with op.batch_alter_table('ledger') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(), nullable=True))
        batch_op.alter_column('merchant_id', existing_type=sa.VARCHAR(), nullable=True)
        batch_op.create_index(op.f('ix_ledger_user_id'), ['user_id'], unique=False)
        batch_op.create_foreign_key('fk_ledger_user_id', 'users', ['user_id'], ['id'])

    # Modify transactions table — batch mode for SQLite
    with op.batch_alter_table('transactions') as batch_op:
        batch_op.add_column(sa.Column('sender_user_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('payment_request_id', sa.String(), nullable=True))
        batch_op.alter_column('sender_merchant_id', existing_type=sa.VARCHAR(), nullable=True)
        batch_op.create_index(op.f('ix_transactions_sender_user_id'), ['sender_user_id'], unique=False)
        batch_op.create_index(op.f('ix_transactions_payment_request_id'), ['payment_request_id'], unique=False)
        batch_op.create_foreign_key('fk_txn_sender_user_id', 'users', ['sender_user_id'], ['id'])
        batch_op.create_foreign_key('fk_txn_payment_request_id', 'payment_requests', ['payment_request_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('transactions') as batch_op:
        batch_op.drop_constraint('fk_txn_payment_request_id', type_='foreignkey')
        batch_op.drop_constraint('fk_txn_sender_user_id', type_='foreignkey')
        batch_op.drop_index(op.f('ix_transactions_sender_user_id'))
        batch_op.drop_index(op.f('ix_transactions_payment_request_id'))
        batch_op.alter_column('sender_merchant_id', existing_type=sa.VARCHAR(), nullable=False)
        batch_op.drop_column('payment_request_id')
        batch_op.drop_column('sender_user_id')

    with op.batch_alter_table('ledger') as batch_op:
        batch_op.drop_constraint('fk_ledger_user_id', type_='foreignkey')
        batch_op.drop_index(op.f('ix_ledger_user_id'))
        batch_op.alter_column('merchant_id', existing_type=sa.VARCHAR(), nullable=False)
        batch_op.drop_column('user_id')

    op.drop_index(op.f('ix_payment_requests_merchant_id'), table_name='payment_requests')
    op.drop_table('payment_requests')
