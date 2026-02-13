import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/transaction.dart';
import '../services/api_client.dart';
import '../services/payment_service.dart';

final paymentServiceProvider = Provider<PaymentService>((ref) {
  final api = ref.read(apiClientProvider);
  return PaymentService(api);
});

final transactionListProvider =
    StateNotifierProvider<TransactionListNotifier, AsyncValue<List<Transaction>>>((ref) {
  final service = ref.read(paymentServiceProvider);
  return TransactionListNotifier(service);
});

class TransactionListNotifier extends StateNotifier<AsyncValue<List<Transaction>>> {
  final PaymentService _service;
  int _page = 1;
  bool _hasMore = true;
  String? _merchantId;

  TransactionListNotifier(this._service) : super(const AsyncValue.loading());

  Future<void> load(String merchantId) async {
    _merchantId = merchantId;
    _page = 1;
    _hasMore = true;
    state = const AsyncValue.loading();
    try {
      final items = await _service.listPayments(merchantId: merchantId, page: 1);
      _hasMore = items.length >= 20;
      state = AsyncValue.data(items);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> loadMore() async {
    if (!_hasMore || _merchantId == null) return;
    _page++;
    try {
      final items = await _service.listPayments(merchantId: _merchantId, page: _page);
      _hasMore = items.length >= 20;
      final current = state.value ?? [];
      state = AsyncValue.data([...current, ...items]);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}
