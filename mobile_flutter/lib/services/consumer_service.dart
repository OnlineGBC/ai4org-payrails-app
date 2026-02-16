import 'package:uuid/uuid.dart';
import '../models/payment_request.dart';
import '../models/wallet_balance.dart';
import '../models/transaction.dart';
import 'api_client.dart';

class ConsumerService {
  final ApiClient _api;

  ConsumerService(this._api);

  Future<PaymentRequest> createPaymentRequest(
    String merchantId,
    double amount,
    String? description,
  ) async {
    final response = await _api.post(
      '/merchants/$merchantId/payment-requests',
      data: {
        'amount': amount.toString(),
        'description': description,
      },
    );
    return PaymentRequest.fromJson(response.data);
  }

  Future<PaymentRequest> getPaymentRequest(String requestId) async {
    final response = await _api.get('/payment-requests/$requestId');
    return PaymentRequest.fromJson(response.data);
  }

  Future<Map<String, dynamic>> consumerPay(
    String paymentRequestId, {
    String? preferredRail,
  }) async {
    final idempotencyKey = const Uuid().v4();
    final response = await _api.post('/consumer/pay', data: {
      'payment_request_id': paymentRequestId,
      'idempotency_key': idempotencyKey,
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
