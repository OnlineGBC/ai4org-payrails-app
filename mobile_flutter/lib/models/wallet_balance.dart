class WalletBalance {
  final String userId;
  final double balance;

  WalletBalance({required this.userId, required this.balance});

  factory WalletBalance.fromJson(Map<String, dynamic> json) {
    return WalletBalance(
      userId: json['user_id'] as String,
      balance: (json['balance'] is String)
          ? double.parse(json['balance'] as String)
          : (json['balance'] as num).toDouble(),
    );
  }
}

class WalletFundResult {
  final String userId;
  final double balance;
  final String transactionStatus;
  final String referenceId;
  final String? failureReason;

  WalletFundResult({
    required this.userId,
    required this.balance,
    required this.transactionStatus,
    required this.referenceId,
    this.failureReason,
  });

  bool get succeeded => transactionStatus == 'completed';

  factory WalletFundResult.fromJson(Map<String, dynamic> json) {
    return WalletFundResult(
      userId: json['user_id'] as String,
      balance: (json['balance'] is String)
          ? double.parse(json['balance'] as String)
          : (json['balance'] as num).toDouble(),
      transactionStatus: json['transaction_status'] as String,
      referenceId: json['reference_id'] as String,
      failureReason: json['failure_reason'] as String?,
    );
  }
}
