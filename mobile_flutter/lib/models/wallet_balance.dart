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
