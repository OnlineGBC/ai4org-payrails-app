"""add_stablecoin_models

Adds multi-asset / stablecoin scaffolding: assets, asset_networks,
crypto_accounts, kyc_records, sanctions_screening; plus additive columns on
ledger and transactions. Seeds the three supported assets (USD, USDC, USD1).

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- reference: assets ---
    op.create_table(
        'assets',
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('asset_type', sa.String(), nullable=False),
        sa.Column('decimals', sa.SmallInteger(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint('code'),
    )
    op.bulk_insert(
        sa.table(
            'assets',
            sa.column('code', sa.String),
            sa.column('asset_type', sa.String),
            sa.column('decimals', sa.SmallInteger),
            sa.column('display_name', sa.String),
            sa.column('is_active', sa.Boolean),
        ),
        [
            {'code': 'USD',  'asset_type': 'fiat',       'decimals': 2, 'display_name': 'US Dollar',          'is_active': True},
            {'code': 'USDC', 'asset_type': 'stablecoin', 'decimals': 6, 'display_name': 'USD Coin',           'is_active': True},
            {'code': 'USD1', 'asset_type': 'stablecoin', 'decimals': 6, 'display_name': 'World Liberty USD1', 'is_active': True},
        ],
    )

    # --- reference: asset_networks ---
    op.create_table(
        'asset_networks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('asset_code', sa.String(), nullable=False),
        sa.Column('network', sa.String(), nullable=False),
        sa.Column('contract_address', sa.String(), nullable=True),
        sa.Column('min_confirmations', sa.SmallInteger(), server_default='12', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.ForeignKeyConstraint(['asset_code'], ['assets.code']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('asset_code', 'network', name='uq_asset_network'),
    )

    # --- custodial crypto accounts ---
    op.create_table(
        'crypto_accounts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('merchant_id', sa.String(), nullable=True),
        sa.Column('partner', sa.String(), nullable=False),
        sa.Column('partner_account_id', sa.String(), nullable=False),
        sa.Column('asset_code', sa.String(), nullable=False),
        sa.Column('network', sa.String(), nullable=False),
        sa.Column('deposit_address', sa.String(), nullable=True),
        sa.Column('status', sa.String(), server_default='pending', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['asset_code'], ['assets.code']),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('partner', 'partner_account_id', 'asset_code', 'network', name='uq_crypto_account'),
    )
    op.create_index('ix_crypto_accounts_user_id', 'crypto_accounts', ['user_id'])

    # --- KYC records ---
    op.create_table(
        'kyc_records',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('partner', sa.String(), nullable=False),
        sa.Column('partner_kyc_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), server_default='not_started', nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_kyc_records_user_id', 'kyc_records', ['user_id'], unique=True)

    # --- sanctions / KYT screening ---
    op.create_table(
        'sanctions_screening',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('transaction_id', sa.String(), nullable=True),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('result', sa.String(), nullable=False),
        sa.Column('risk_score', sa.Numeric(6, 2), nullable=True),
        sa.Column('raw_payload', sa.Text(), nullable=True),
        sa.Column('screened_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_sanctions_screening_transaction_id', 'sanctions_screening', ['transaction_id'])

    # --- ledger: multi-asset + base-unit columns ---
    with op.batch_alter_table('ledger', schema=None) as batch_op:
        batch_op.add_column(sa.Column('asset_code', sa.String(), server_default='USD', nullable=False))
        batch_op.add_column(sa.Column('amount_base_units', sa.Numeric(38, 0), nullable=True))
        batch_op.add_column(sa.Column('balance_after_base_units', sa.Numeric(38, 0), nullable=True))
        batch_op.create_foreign_key('fk_ledger_asset_code', 'assets', ['asset_code'], ['code'])
    op.create_index('ix_ledger_owner_asset', 'ledger', ['merchant_id', 'user_id', 'asset_code'])

    # --- transactions: asset + on-chain settlement columns ---
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('asset_code', sa.String(), server_default='USD', nullable=False))
        batch_op.add_column(sa.Column('amount_base_units', sa.Numeric(38, 0), nullable=True))
        batch_op.add_column(sa.Column('settlement_type', sa.String(), server_default='offchain', nullable=False))
        batch_op.add_column(sa.Column('settlement_network', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('onchain_tx_hash', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('onchain_status', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('confirmations', sa.Integer(), server_default='0', nullable=True))
        batch_op.add_column(sa.Column('partner', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('partner_transfer_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('direction', sa.String(), nullable=True))
        batch_op.create_foreign_key('fk_transactions_asset_code', 'assets', ['asset_code'], ['code'])
        batch_op.create_unique_constraint('uq_transactions_onchain_tx_hash', ['onchain_tx_hash'])
    op.create_index('ix_transactions_partner_transfer_id', 'transactions', ['partner_transfer_id'])


def downgrade() -> None:
    op.drop_index('ix_transactions_partner_transfer_id', table_name='transactions')
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.drop_constraint('uq_transactions_onchain_tx_hash', type_='unique')
        batch_op.drop_constraint('fk_transactions_asset_code', type_='foreignkey')
        batch_op.drop_column('direction')
        batch_op.drop_column('partner_transfer_id')
        batch_op.drop_column('partner')
        batch_op.drop_column('confirmations')
        batch_op.drop_column('onchain_status')
        batch_op.drop_column('onchain_tx_hash')
        batch_op.drop_column('settlement_network')
        batch_op.drop_column('settlement_type')
        batch_op.drop_column('amount_base_units')
        batch_op.drop_column('asset_code')

    op.drop_index('ix_ledger_owner_asset', table_name='ledger')
    with op.batch_alter_table('ledger', schema=None) as batch_op:
        batch_op.drop_constraint('fk_ledger_asset_code', type_='foreignkey')
        batch_op.drop_column('balance_after_base_units')
        batch_op.drop_column('amount_base_units')
        batch_op.drop_column('asset_code')

    op.drop_index('ix_sanctions_screening_transaction_id', table_name='sanctions_screening')
    op.drop_table('sanctions_screening')
    op.drop_index('ix_kyc_records_user_id', table_name='kyc_records')
    op.drop_table('kyc_records')
    op.drop_index('ix_crypto_accounts_user_id', table_name='crypto_accounts')
    op.drop_table('crypto_accounts')
    op.drop_table('asset_networks')
    op.drop_table('assets')
