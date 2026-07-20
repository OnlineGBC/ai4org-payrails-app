"""relax legacy Decimal amount columns to nullable

Stablecoin ledger/transaction rows carry value in the integer base-unit columns,
so the legacy USD-only Decimal columns (ledger.amount, ledger.balance_after,
transactions.amount) become nullable rather than storing lossy 2-decimal values.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('ledger', schema=None) as batch_op:
        batch_op.alter_column('amount', existing_type=sa.Numeric(12, 2), nullable=True)
        batch_op.alter_column('balance_after', existing_type=sa.Numeric(12, 2), nullable=True)
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.alter_column('amount', existing_type=sa.Numeric(12, 2), nullable=True)


def downgrade() -> None:
    # Best-effort: only valid if no NULL rows exist.
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.alter_column('amount', existing_type=sa.Numeric(12, 2), nullable=False)
    with op.batch_alter_table('ledger', schema=None) as batch_op:
        batch_op.alter_column('balance_after', existing_type=sa.Numeric(12, 2), nullable=False)
        batch_op.alter_column('amount', existing_type=sa.Numeric(12, 2), nullable=False)
