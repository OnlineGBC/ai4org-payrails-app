import 'package:dio/dio.dart';
import '../models/stablecoin.dart';
import 'api_client.dart';

/// Extracts a user-facing message from a stablecoin API error
/// (e.g. the FastAPI `detail` field for 400/403 responses).
String stablecoinErrorMessage(Object e) {
  if (e is DioException) {
    final data = e.response?.data;
    if (data is Map && data['detail'] != null) return data['detail'].toString();
    return e.message ?? 'Network error';
  }
  return e.toString();
}

class StablecoinService {
  final ApiClient _api;

  StablecoinService(this._api);

  Future<String> getKycStatus() async {
    final r = await _api.get('/stablecoin/kyc');
    return r.data['status'] as String;
  }

  Future<String> submitKyc({
    String? firstName,
    String? lastName,
    String? country,
  }) async {
    final r = await _api.post('/stablecoin/kyc', data: {
      if (firstName != null) 'first_name': firstName,
      if (lastName != null) 'last_name': lastName,
      if (country != null) 'country': country,
    });
    return r.data['status'] as String;
  }

  Future<List<StablecoinBalance>> getBalances() async {
    final r = await _api.get('/stablecoin/balances');
    final list = r.data['balances'] as List;
    return list
        .map((e) => StablecoinBalance.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<CryptoAccount>> listAccounts() async {
    final r = await _api.get('/stablecoin/accounts');
    final list = r.data as List;
    return list
        .map((e) => CryptoAccount.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<CryptoAccount> createAccount(String assetCode, String network) async {
    final r = await _api.post('/stablecoin/accounts',
        data: {'asset_code': assetCode, 'network': network});
    return CryptoAccount.fromJson(r.data as Map<String, dynamic>);
  }

  Future<StablecoinTx> onramp(
      double usdAmount, String assetCode, String network) async {
    final r = await _api.post('/stablecoin/onramp', data: {
      'usd_amount': usdAmount.toString(),
      'asset_code': assetCode,
      'network': network,
    });
    return StablecoinTx.fromJson(r.data as Map<String, dynamic>);
  }

  Future<StablecoinTx> offramp(
      double amount, String assetCode, String network) async {
    final r = await _api.post('/stablecoin/offramp', data: {
      'amount': amount.toString(),
      'asset_code': assetCode,
      'network': network,
    });
    return StablecoinTx.fromJson(r.data as Map<String, dynamic>);
  }

  Future<StablecoinTx> send(
      String toAddress, double amount, String assetCode, String network) async {
    final r = await _api.post('/stablecoin/send', data: {
      'to_address': toAddress,
      'amount': amount.toString(),
      'asset_code': assetCode,
      'network': network,
    });
    return StablecoinTx.fromJson(r.data as Map<String, dynamic>);
  }

  Future<List<StablecoinTx>> listTransactions({String? assetCode}) async {
    final r = await _api.get('/stablecoin/transactions',
        queryParameters: assetCode != null ? {'asset_code': assetCode} : null);
    final list = r.data as List;
    return list
        .map((e) => StablecoinTx.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
