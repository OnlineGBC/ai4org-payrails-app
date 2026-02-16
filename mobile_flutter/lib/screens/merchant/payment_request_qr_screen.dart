import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../../widgets/payrails_app_bar.dart';

class PaymentRequestQrScreen extends StatelessWidget {
  final String requestId;
  final String amount;
  final String description;

  const PaymentRequestQrScreen({
    super.key,
    required this.requestId,
    required this.amount,
    required this.description,
  });

  @override
  Widget build(BuildContext context) {
    final qrData = 'payrails://pay-request?id=$requestId';

    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Payment QR Code'),
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
              const SizedBox(height: 8),
              Text(
                '\$$amount',
                style: Theme.of(context)
                    .textTheme
                    .headlineMedium
                    ?.copyWith(fontWeight: FontWeight.bold),
              ),
              if (description.isNotEmpty) ...[
                const SizedBox(height: 4),
                Text(
                  description,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
              const SizedBox(height: 24),
              QrImageView(
                data: qrData,
                version: QrVersions.auto,
                size: 250.0,
                backgroundColor: Colors.white,
              ),
              const SizedBox(height: 24),
              Text(
                'Show this QR code to the customer',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
