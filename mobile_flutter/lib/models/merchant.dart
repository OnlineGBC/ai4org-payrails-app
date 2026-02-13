class Merchant {
  final String id;
  final String name;
  final String? ein;
  final String contactEmail;
  final String? contactPhone;
  final String onboardingStatus;
  final String kybStatus;
  final String? sponsorBankId;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  Merchant({
    required this.id,
    required this.name,
    this.ein,
    required this.contactEmail,
    this.contactPhone,
    required this.onboardingStatus,
    required this.kybStatus,
    this.sponsorBankId,
    this.createdAt,
    this.updatedAt,
  });

  factory Merchant.fromJson(Map<String, dynamic> json) {
    return Merchant(
      id: json['id'] as String,
      name: json['name'] as String,
      ein: json['ein'] as String?,
      contactEmail: json['contact_email'] as String,
      contactPhone: json['contact_phone'] as String?,
      onboardingStatus: json['onboarding_status'] as String,
      kybStatus: json['kyb_status'] as String,
      sponsorBankId: json['sponsor_bank_id'] as String?,
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
        'name': name,
        'ein': ein,
        'contact_email': contactEmail,
        'contact_phone': contactPhone,
        'onboarding_status': onboardingStatus,
        'kyb_status': kybStatus,
        'sponsor_bank_id': sponsorBankId,
      };
}
