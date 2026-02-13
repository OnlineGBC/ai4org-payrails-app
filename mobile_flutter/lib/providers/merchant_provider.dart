import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/merchant.dart';
import '../services/api_client.dart';
import '../services/merchant_service.dart';

final merchantServiceProvider = Provider<MerchantService>((ref) {
  final api = ref.read(apiClientProvider);
  return MerchantService(api);
});

final merchantProvider =
    StateNotifierProvider<MerchantNotifier, AsyncValue<Merchant?>>((ref) {
  final service = ref.read(merchantServiceProvider);
  return MerchantNotifier(service);
});

class MerchantNotifier extends StateNotifier<AsyncValue<Merchant?>> {
  final MerchantService _service;

  MerchantNotifier(this._service) : super(const AsyncValue.data(null));

  Future<void> load(String merchantId) async {
    state = const AsyncValue.loading();
    try {
      final merchant = await _service.getMerchant(merchantId);
      state = AsyncValue.data(merchant);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}
