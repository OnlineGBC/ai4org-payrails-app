import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/payrails_app_bar.dart';

class ConsumerQrScreen extends ConsumerWidget {
  const ConsumerQrScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authStateProvider).user;
    final merchantId = user?.merchantId;
    final displayName = user?.email ?? user?.id ?? 'unknown';

    // If consumer has a merchant profile, use the merchant pay QR.
    // Otherwise fall back to the wallet-receive QR.
    final String qrData;
    final String idLabel;
    final String idValue;
    final String copyLabel;

    if (merchantId != null && merchantId.isNotEmpty) {
      qrData = 'payrails://pay?merchant=${Uri.encodeComponent(merchantId)}';
      idLabel = 'Merchant ID';
      idValue = merchantId;
      copyLabel = 'Copy Merchant ID';
    } else {
      final userId = user?.id ?? 'unknown';
      qrData =
          'payrails://receive?user=${Uri.encodeComponent(userId)}&name=${Uri.encodeComponent(displayName)}';
      idLabel = 'User ID';
      idValue = userId;
      copyLabel = 'Copy User ID';
    }

    return Scaffold(
      appBar: const PayRailsAppBar(title: 'My QR Code'),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                'Show this QR to receive money',
                style: Theme.of(context).textTheme.titleLarge,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                'Anyone with the PayRails app can scan this\nto send money directly to your account.',
                style: Theme.of(context)
                    .textTheme
                    .bodySmall
                    ?.copyWith(color: Colors.grey),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: const [
                    BoxShadow(
                        color: Colors.black12,
                        blurRadius: 12,
                        offset: Offset(0, 4)),
                  ],
                ),
                child: QrImageView(
                  data: qrData,
                  version: QrVersions.auto,
                  size: 240.0,
                  backgroundColor: Colors.white,
                ),
              ),
              const SizedBox(height: 24),
              Text(
                displayName,
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 4),
              Text(
                idLabel,
                style: Theme.of(context).textTheme.bodySmall,
              ),
              const SizedBox(height: 2),
              SelectableText(
                idValue,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      fontFamily: 'monospace',
                      color: Colors.grey,
                    ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 12),
              TextButton.icon(
                onPressed: () {
                  Clipboard.setData(ClipboardData(text: idValue));
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('$idLabel copied')),
                  );
                },
                icon: const Icon(Icons.copy, size: 16),
                label: Text(copyLabel),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
