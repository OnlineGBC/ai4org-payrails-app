import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/stablecoin.dart';
import '../services/api_client.dart';
import '../services/stablecoin_service.dart';

final stablecoinServiceProvider = Provider<StablecoinService>((ref) {
  return StablecoinService(ref.read(apiClientProvider));
});

class StablecoinWalletState {
  final String kycStatus;
  final List<StablecoinBalance> balances;
  final List<CryptoAccount> accounts;

  StablecoinWalletState({
    required this.kycStatus,
    required this.balances,
    required this.accounts,
  });

  bool get kycApproved => kycStatus == 'approved';
}

final stablecoinWalletProvider = StateNotifierProvider<StablecoinWalletNotifier,
    AsyncValue<StablecoinWalletState>>((ref) {
  return StablecoinWalletNotifier(ref.read(stablecoinServiceProvider));
});

class StablecoinWalletNotifier
    extends StateNotifier<AsyncValue<StablecoinWalletState>> {
  final StablecoinService _service;

  StablecoinWalletNotifier(this._service) : super(const AsyncValue.loading());

  Future<void> load() async {
    state = const AsyncValue.loading();
    try {
      final kyc = await _service.getKycStatus();
      final balances = await _service.getBalances();
      final accounts = await _service.listAccounts();
      state = AsyncValue.data(StablecoinWalletState(
        kycStatus: kyc,
        balances: balances,
        accounts: accounts,
      ));
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> submitKyc() async {
    await _service.submitKyc();
    await load();
  }
}
