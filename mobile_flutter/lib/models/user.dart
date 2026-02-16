class User {
  final String id;
  final String email;
  final String role;
  final String? merchantId;
  final DateTime? createdAt;

  User({
    required this.id,
    required this.email,
    required this.role,
    this.merchantId,
    this.createdAt,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as String,
      email: json['email'] as String,
      role: json['role'] as String,
      merchantId: json['merchant_id'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : null,
    );
  }

  bool get isConsumer => role == 'user';
  bool get isMerchant => role == 'merchant_admin';

  Map<String, dynamic> toJson() => {
        'id': id,
        'email': email,
        'role': role,
        'merchant_id': merchantId,
      };
}
