import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/balance.dart';
import '../services/payment_service.dart';
import 'payment_provider.dart';

final balanceProvider =
    StateNotifierProvider<BalanceNotifier, AsyncValue<Balance?>>((ref) {
  final service = ref.read(paymentServiceProvider);
  return BalanceNotifier(service);
});

class BalanceNotifier extends StateNotifier<AsyncValue<Balance?>> {
  final PaymentService _service;

  BalanceNotifier(this._service) : super(const AsyncValue.data(null));

  Future<void> load(String merchantId) async {
    state = const AsyncValue.loading();
    try {
      final balance = await _service.getBalance(merchantId);
      state = AsyncValue.data(balance);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}
