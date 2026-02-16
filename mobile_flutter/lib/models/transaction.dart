class Transaction {
  final String id;
  final String? senderMerchantId;
  final String? senderUserId;
  final String receiverMerchantId;
  final double amount;
  final String currency;
  final String? rail;
  final String status;
  final String idempotencyKey;
  final String? referenceId;
  final String? failureReason;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  Transaction({
    required this.id,
    this.senderMerchantId,
    this.senderUserId,
    required this.receiverMerchantId,
    required this.amount,
    this.currency = 'USD',
    this.rail,
    required this.status,
    required this.idempotencyKey,
    this.referenceId,
    this.failureReason,
    this.createdAt,
    this.updatedAt,
  });

  factory Transaction.fromJson(Map<String, dynamic> json) {
    return Transaction(
      id: json['id'] as String,
      senderMerchantId: json['sender_merchant_id'] as String?,
      senderUserId: json['sender_user_id'] as String?,
      receiverMerchantId: json['receiver_merchant_id'] as String,
      amount: (json['amount'] is String)
          ? double.parse(json['amount'] as String)
          : (json['amount'] as num).toDouble(),
      currency: json['currency'] as String? ?? 'USD',
      rail: json['rail'] as String?,
      status: json['status'] as String,
      idempotencyKey: json['idempotency_key'] as String,
      referenceId: json['reference_id'] as String?,
      failureReason: json['failure_reason'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : null,
      updatedAt: json['updated_at'] != null
          ? DateTime.parse(json['updated_at'] as String)
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'sender_merchant_id': senderMerchantId,
        'receiver_merchant_id': receiverMerchantId,
        'amount': amount.toString(),
        'currency': currency,
        'rail': rail,
        'status': status,
        'idempotency_key': idempotencyKey,
      };
}
