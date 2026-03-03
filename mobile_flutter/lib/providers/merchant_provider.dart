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

  /// Returns null on success, or an error message string on failure.
  Future<String?> submitKyb(
    String merchantId, {
    required String ein,
    required String businessName,
    String? businessAddress,
    String? representativeName,
    String? representativeSsnLast4,
  }) async {
    try {
      final updated = await _service.submitKyb(
        merchantId,
        ein: ein,
        businessName: businessName,
        businessAddress: businessAddress,
        representativeName: representativeName,
        representativeSsnLast4: representativeSsnLast4,
      );
      state = AsyncValue.data(updated);
      return null;
    } catch (e) {
      return e.toString();
    }
  }
}
