import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/wallet_balance.dart';
import '../models/transaction.dart';
import '../services/api_client.dart';
import '../services/consumer_service.dart';
import '../services/payment_service.dart';

final consumerServiceProvider = Provider<ConsumerService>((ref) {
  final api = ref.read(apiClientProvider);
  return ConsumerService(api);
});

final _paymentServiceForConsumerProvider = Provider<PaymentService>((ref) {
  final api = ref.read(apiClientProvider);
  return PaymentService(api);
});

final consumerTransactionListProvider = StateNotifierProvider<
    ConsumerTransactionListNotifier, AsyncValue<List<Transaction>>>((ref) {
  final service = ref.read(_paymentServiceForConsumerProvider);
  return ConsumerTransactionListNotifier(service);
});

class ConsumerTransactionListNotifier
    extends StateNotifier<AsyncValue<List<Transaction>>> {
  final PaymentService _service;

  ConsumerTransactionListNotifier(this._service)
      : super(const AsyncValue.data([]));

  Future<void> load(String userId) async {
    state = const AsyncValue.loading();
    try {
      final txns = await _service.listPayments(userId: userId, pageSize: 5);
      state = AsyncValue.data(txns);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}

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
