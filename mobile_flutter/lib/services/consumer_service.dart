import 'package:uuid/uuid.dart';
import '../models/wallet_balance.dart';
import '../models/transaction.dart';
import 'api_client.dart';

class ConsumerService {
  final ApiClient _api;

  ConsumerService(this._api);

  Future<Map<String, dynamic>> getMerchantInfo(String merchantId) async {
    final response = await _api.get('/merchants/$merchantId/status');
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> consumerPay(
    String merchantId,
    double amount, {
    String? description,
    String? preferredRail,
  }) async {
    final idempotencyKey = const Uuid().v4();
    final response = await _api.post('/consumer/pay', data: {
      'merchant_id': merchantId,
      'amount': amount.toString(),
      'idempotency_key': idempotencyKey,
      if (description != null) 'description': description,
      if (preferredRail != null) 'preferred_rail': preferredRail,
    });
    return response.data as Map<String, dynamic>;
  }

  Future<WalletBalance> getWalletBalance() async {
    final response = await _api.get('/consumer/wallet/balance');
    return WalletBalance.fromJson(response.data);
  }

  Future<WalletBalance> topUpWallet(double amount) async {
    final response = await _api.post(
      '/consumer/wallet/topup',
      queryParameters: {'amount': amount.toString()},
    );
    return WalletBalance.fromJson(response.data);
  }

  Future<List<Transaction>> listConsumerTransactions({
    int page = 1,
    int pageSize = 20,
  }) async {
    final response = await _api.get('/payments', queryParameters: {
      'page': page,
      'page_size': pageSize,
    });
    final items = response.data['items'] as List;
    return items.map((e) => Transaction.fromJson(e)).toList();
  }
}
