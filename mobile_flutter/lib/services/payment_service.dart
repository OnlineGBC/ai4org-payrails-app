import '../config/api_config.dart';
import '../models/transaction.dart';
import '../models/balance.dart';
import 'api_client.dart';

class PaymentService {
  final ApiClient _api;

  PaymentService(this._api);

  Future<Transaction> sendPayment({
    required String senderMerchantId,
    required String receiverMerchantId,
    required double amount,
    required String idempotencyKey,
    String? preferredRail,
  }) async {
    final response = await _api.post(ApiConfig.payments, data: {
      'sender_merchant_id': senderMerchantId,
      'receiver_merchant_id': receiverMerchantId,
      'amount': amount.toString(),
      'idempotency_key': idempotencyKey,
      if (preferredRail != null) 'preferred_rail': preferredRail,
    });
    return Transaction.fromJson(response.data);
  }

  Future<Transaction> getPayment(String paymentId) async {
    final response = await _api.get('${ApiConfig.payments}/$paymentId');
    return Transaction.fromJson(response.data);
  }

  Future<List<Transaction>> listPayments({
    String? merchantId,
    String? status,
    String? rail,
    int page = 1,
    int pageSize = 20,
  }) async {
    final response = await _api.get(ApiConfig.payments, queryParameters: {
      if (merchantId != null) 'merchant_id': merchantId,
      if (status != null) 'status': status,
      if (rail != null) 'rail': rail,
      'page': page,
      'page_size': pageSize,
    });
    final items = response.data['items'] as List;
    return items.map((e) => Transaction.fromJson(e)).toList();
  }

  Future<Balance> getBalance(String merchantId) async {
    final response = await _api.get(ApiConfig.balance, queryParameters: {
      'merchant_id': merchantId,
    });
    return Balance.fromJson(response.data);
  }

  Future<Transaction> cancelPayment(String paymentId) async {
    final response = await _api.post('${ApiConfig.payments}/$paymentId/cancel');
    return Transaction.fromJson(response.data);
  }
}
