class PaymentRequest {
  final String id;
  final String merchantId;
  final String? merchantName;
  final double amount;
  final String currency;
  final String? description;
  final String status;
  final DateTime? expiresAt;
  final DateTime? createdAt;

  PaymentRequest({
    required this.id,
    required this.merchantId,
    this.merchantName,
    required this.amount,
    required this.currency,
    this.description,
    required this.status,
    this.expiresAt,
    this.createdAt,
  });

  factory PaymentRequest.fromJson(Map<String, dynamic> json) {
    return PaymentRequest(
      id: json['id'] as String,
      merchantId: json['merchant_id'] as String,
      merchantName: json['merchant_name'] as String?,
      amount: (json['amount'] is String)
          ? double.parse(json['amount'] as String)
          : (json['amount'] as num).toDouble(),
      currency: json['currency'] as String? ?? 'USD',
      description: json['description'] as String?,
      status: json['status'] as String,
      expiresAt: json['expires_at'] != null
          ? DateTime.parse(json['expires_at'] as String)
          : null,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : null,
    );
  }
}
