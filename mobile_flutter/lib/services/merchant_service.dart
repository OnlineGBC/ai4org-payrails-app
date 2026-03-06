import '../config/api_config.dart';
import '../models/bank_config.dart';
import '../models/merchant.dart';
import '../models/bank_account.dart';
import 'api_client.dart';

class MerchantService {
  final ApiClient _api;

  MerchantService(this._api);

  Future<List<BankConfig>> getSupportedBanks() async {
    final response = await _api.get('/banks');
    final items = response.data as List;
    return items.map((e) => BankConfig.fromJson(e)).toList();
  }

  Future<Merchant> getMerchant(String merchantId) async {
    final response = await _api.get('${ApiConfig.merchants}/$merchantId/status');
    return Merchant.fromJson(response.data);
  }

  Future<Merchant> updateMerchant(String merchantId, Map<String, dynamic> data) async {
    final response = await _api.put('${ApiConfig.merchants}/$merchantId', data: data);
    return Merchant.fromJson(response.data);
  }

  Future<List<BankAccount>> listBankAccounts(String merchantId) async {
    final response = await _api.get('${ApiConfig.merchants}/$merchantId/bank-accounts');
    final items = response.data as List;
    return items.map((e) => BankAccount.fromJson(e)).toList();
  }

  Future<BankAccount> addBankAccount(
    String merchantId, {
    required String routingNumber,
    required String accountNumber,
    required String bankName,
    String accountType = 'checking',
  }) async {
    final response = await _api.post(
      '${ApiConfig.merchants}/$merchantId/bank-accounts',
      data: {
        'routing_number': routingNumber,
        'account_number': accountNumber,
        'account_type': accountType,
        'bank_name': bankName,
      },
    );
    return BankAccount.fromJson(response.data);
  }

  Future<BankAccount> verifyMicroDeposits(
    String merchantId,
    String accountId, {
    required String amount1,
    required String amount2,
  }) async {
    final response = await _api.post(
      '${ApiConfig.merchants}/$merchantId/bank-accounts/$accountId/verify-micro-deposits',
      data: {'amount_1': amount1, 'amount_2': amount2},
    );
    return BankAccount.fromJson(response.data);
  }

  Future<BankAccount> verifyInstant(String merchantId, String accountId) async {
    final response = await _api.post(
      '${ApiConfig.merchants}/$merchantId/bank-accounts/$accountId/verify-instant',
    );
    return BankAccount.fromJson(response.data);
  }

  Future<Merchant> submitKyb(
    String merchantId, {
    required String ein,
    required String businessName,
    String? businessAddress,
    String? representativeName,
    String? representativeSsnLast4,
  }) async {
    final response = await _api.post(
      '${ApiConfig.merchants}/$merchantId/kyb',
      data: {
        'ein': ein,
        'business_name': businessName,
        if (businessAddress != null) 'business_address': businessAddress,
        if (representativeName != null) 'representative_name': representativeName,
        if (representativeSsnLast4 != null)
          'representative_ssn_last4': representativeSsnLast4,
      },
    );
    return Merchant.fromJson(response.data);
  }
}
