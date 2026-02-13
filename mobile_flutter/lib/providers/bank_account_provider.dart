import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/bank_account.dart';
import '../services/merchant_service.dart';
import 'merchant_provider.dart';

final bankAccountListProvider =
    StateNotifierProvider<BankAccountListNotifier, AsyncValue<List<BankAccount>>>((ref) {
  final service = ref.read(merchantServiceProvider);
  return BankAccountListNotifier(service);
});

class BankAccountListNotifier extends StateNotifier<AsyncValue<List<BankAccount>>> {
  final MerchantService _service;

  BankAccountListNotifier(this._service) : super(const AsyncValue.data([]));

  Future<void> load(String merchantId) async {
    state = const AsyncValue.loading();
    try {
      final accounts = await _service.listBankAccounts(merchantId);
      state = AsyncValue.data(accounts);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}
