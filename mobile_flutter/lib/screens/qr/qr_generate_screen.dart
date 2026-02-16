import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/payrails_app_bar.dart';

class QrGenerateScreen extends ConsumerWidget {
  const QrGenerateScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authStateProvider).user;
    final merchantId = user?.merchantId ?? 'unknown';
    final qrData = 'payrails://pay?merchant=$merchantId';

    return Scaffold(
      appBar: const PayRailsAppBar(title: 'My QR Code'),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                'Show this QR to receive payment',
                style: Theme.of(context).textTheme.titleLarge,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              QrImageView(
                data: qrData,
                version: QrVersions.auto,
                size: 250.0,
                backgroundColor: Colors.white,
              ),
              const SizedBox(height: 24),
              Text(
                'Merchant ID:',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              const SizedBox(height: 4),
              SelectableText(
                merchantId,
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      fontFamily: 'monospace',
                      fontWeight: FontWeight.bold,
                    ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 12),
              TextButton.icon(
                onPressed: () {
                  Clipboard.setData(ClipboardData(text: merchantId));
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Merchant ID copied')),
                  );
                },
                icon: const Icon(Icons.copy, size: 16),
                label: const Text('Copy ID'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
