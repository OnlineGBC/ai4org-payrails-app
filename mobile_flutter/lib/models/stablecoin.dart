double _toDouble(dynamic v) =>
    v is String ? double.parse(v) : (v as num).toDouble();

class StablecoinBalance {
  final String assetCode;
  final double balance;

  StablecoinBalance({required this.assetCode, required this.balance});

  factory StablecoinBalance.fromJson(Map<String, dynamic> json) =>
      StablecoinBalance(
        assetCode: json['asset_code'] as String,
        balance: _toDouble(json['balance']),
      );
}

class CryptoAccount {
  final String id;
  final String assetCode;
  final String network;
  final String status;
  final String? depositAddress;

  CryptoAccount({
    required this.id,
    required this.assetCode,
    required this.network,
    required this.status,
    this.depositAddress,
  });

  factory CryptoAccount.fromJson(Map<String, dynamic> json) => CryptoAccount(
        id: json['id'] as String,
        assetCode: json['asset_code'] as String,
        network: json['network'] as String,
        status: json['status'] as String,
        depositAddress: json['deposit_address'] as String?,
      );
}

class StablecoinTx {
  final String id;
  final String direction;
  final String assetCode;
  final double amount;
  final String status;
  final String? onchainStatus;
  final String? onchainTxHash;
  final String? network;
  final String? createdAt;

  StablecoinTx({
    required this.id,
    required this.direction,
    required this.assetCode,
    required this.amount,
    required this.status,
    this.onchainStatus,
    this.onchainTxHash,
    this.network,
    this.createdAt,
  });

  factory StablecoinTx.fromJson(Map<String, dynamic> json) => StablecoinTx(
        id: json['id'] as String,
        direction: json['direction'] as String? ?? '',
        assetCode: json['asset_code'] as String? ?? '',
        amount: _toDouble(json['amount'] ?? '0'),
        status: json['status'] as String? ?? '',
        onchainStatus: json['onchain_status'] as String?,
        onchainTxHash: json['onchain_tx_hash'] as String?,
        network: json['network'] as String?,
        createdAt: json['created_at'] as String?,
      );
}
