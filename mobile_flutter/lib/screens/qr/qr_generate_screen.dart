import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../../providers/auth_provider.dart';
import '../../router/route_names.dart';
import '../../widgets/payrails_app_bar.dart';

class QrGenerateScreen extends ConsumerWidget {
  const QrGenerateScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authStateProvider).user;

    // For merchants, redirect to the payment request flow
    if (user?.isMerchant == true) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        context.pushReplacement(RouteNames.merchantCreatePaymentRequest);
      });
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    final merchantId = user?.merchantId ?? 'unknown';
    final qrData = 'payrails://pay?merchant=$merchantId';

    return Scaffold(
      appBar: const PayRailsAppBar(title: 'QR Payment Code'),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                'Scan to Pay',
                style: Theme.of(context).textTheme.titleLarge,
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
                'Merchant: $merchantId',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
