import 'package:flutter_test/flutter_test.dart';
import 'package:instant_pay_app/models/stablecoin.dart';

void main() {
  group('StablecoinBalance.fromJson', () {
    test('parses string balance', () {
      final b = StablecoinBalance.fromJson({'asset_code': 'USDC', 'balance': '100.5'});
      expect(b.assetCode, 'USDC');
      expect(b.balance, 100.5);
    });

    test('parses numeric balance', () {
      final b = StablecoinBalance.fromJson({'asset_code': 'USD1', 'balance': 42});
      expect(b.assetCode, 'USD1');
      expect(b.balance, 42.0);
    });
  });

  test('CryptoAccount.fromJson parses fields', () {
    final a = CryptoAccount.fromJson({
      'id': 'acct-1',
      'asset_code': 'USDC',
      'network': 'ethereum',
      'status': 'active',
      'deposit_address': '0xabc',
    });
    expect(a.id, 'acct-1');
    expect(a.network, 'ethereum');
    expect(a.depositAddress, '0xabc');
  });

  test('StablecoinTx.fromJson parses on-chain fields and string amount', () {
    final t = StablecoinTx.fromJson({
      'id': 'tx-1',
      'direction': 'onramp',
      'asset_code': 'USDC',
      'amount': '100.000000',
      'status': 'completed',
      'onchain_status': 'confirmed',
      'onchain_tx_hash': '0xhash',
      'network': 'ethereum',
      'created_at': '2026-07-19T00:00:00',
    });
    expect(t.direction, 'onramp');
    expect(t.amount, 100.0);
    expect(t.onchainTxHash, '0xhash');
  });

  test('StablecoinTx.fromJson tolerates missing optional fields', () {
    final t = StablecoinTx.fromJson({'id': 'tx-2'});
    expect(t.id, 'tx-2');
    expect(t.amount, 0.0);
    expect(t.onchainTxHash, isNull);
  });
}
