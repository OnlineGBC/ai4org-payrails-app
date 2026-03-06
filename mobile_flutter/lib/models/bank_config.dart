class BankConfig {
  final String id;
  final String bankName;
  final List<String> supportedRails;

  BankConfig({
    required this.id,
    required this.bankName,
    required this.supportedRails,
  });

  factory BankConfig.fromJson(Map<String, dynamic> json) {
    return BankConfig(
      id: json['id'] as String,
      bankName: json['bank_name'] as String,
      supportedRails: (json['supported_rails'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
    );
  }
}
