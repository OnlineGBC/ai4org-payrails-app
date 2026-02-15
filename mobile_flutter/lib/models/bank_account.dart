class BankAccount {
  final String id;
  final String merchantId;
  final String? bankName;
  final String routingNumber;
  final String? accountNumberLast4;
  final String accountType;
  final String verificationStatus;
  final String? microDepositAmount1;
  final String? microDepositAmount2;
  final DateTime? createdAt;

  BankAccount({
    required this.id,
    required this.merchantId,
    this.bankName,
    required this.routingNumber,
    this.accountNumberLast4,
    required this.accountType,
    required this.verificationStatus,
    this.microDepositAmount1,
    this.microDepositAmount2,
    this.createdAt,
  });

  factory BankAccount.fromJson(Map<String, dynamic> json) {
    return BankAccount(
      id: json['id'] as String,
      merchantId: json['merchant_id'] as String,
      bankName: json['bank_name'] as String?,
      routingNumber: json['routing_number'] as String,
      accountNumberLast4: json['account_number_last4'] as String?,
      accountType: json['account_type'] as String,
      verificationStatus: json['verification_status'] as String,
      microDepositAmount1: json['micro_deposit_amount_1'] as String?,
      microDepositAmount2: json['micro_deposit_amount_2'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'merchant_id': merchantId,
        'bank_name': bankName,
        'routing_number': routingNumber,
        'account_number_last4': accountNumberLast4,
        'account_type': accountType,
        'verification_status': verificationStatus,
      };
}
