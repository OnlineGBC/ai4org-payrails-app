import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/wallet_balance.dart';
import '../services/api_client.dart';
import '../services/consumer_service.dart';

final consumerServiceProvider = Provider<ConsumerService>((ref) {
  final api = ref.read(apiClientProvider);
  return ConsumerService(api);
});

final walletBalanceProvider =
    StateNotifierProvider<WalletBalanceNotifier, AsyncValue<WalletBalance?>>(
        (ref) {
  final service = ref.read(consumerServiceProvider);
  return WalletBalanceNotifier(service);
});

class WalletBalanceNotifier extends StateNotifier<AsyncValue<WalletBalance?>> {
  final ConsumerService _service;

  WalletBalanceNotifier(this._service) : super(const AsyncValue.data(null));

  Future<void> load() async {
    state = const AsyncValue.loading();
    try {
      final balance = await _service.getWalletBalance();
      state = AsyncValue.data(balance);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> topUp(double amount) async {
    try {
      final balance = await _service.topUpWallet(amount);
      state = AsyncValue.data(balance);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}
