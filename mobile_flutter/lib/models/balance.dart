class Balance {
  final String merchantId;
  final double balance;

  Balance({required this.merchantId, required this.balance});

  factory Balance.fromJson(Map<String, dynamic> json) {
    return Balance(
      merchantId: json['merchant_id'] as String,
      balance: (json['balance'] is String)
          ? double.parse(json['balance'] as String)
          : (json['balance'] as num).toDouble(),
    );
  }
}
