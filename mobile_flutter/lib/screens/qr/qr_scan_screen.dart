import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../../router/route_names.dart';
import '../../widgets/payrails_app_bar.dart';

class QrScanScreen extends StatefulWidget {
  const QrScanScreen({super.key});

  @override
  State<QrScanScreen> createState() => _QrScanScreenState();
}

class _QrScanScreenState extends State<QrScanScreen> {
  bool _scanned = false;

  void _onDetect(BarcodeCapture capture) {
    if (_scanned) return;
    final barcode = capture.barcodes.firstOrNull;
    if (barcode?.rawValue == null) return;

    setState(() => _scanned = true);

    final data = barcode!.rawValue!;
    final uri = Uri.tryParse(data);

    if (uri != null && uri.scheme == 'payrails') {
      if (uri.host == 'pay-request') {
        // B2C2B payment request QR: payrails://pay-request?id=<requestId>
        final requestId = uri.queryParameters['id'];
        if (requestId != null) {
          context.push(
            '${RouteNames.consumerPayConfirm}?requestId=$requestId',
          );
          return;
        }
      } else if (uri.host == 'pay') {
        // Legacy M2M QR: payrails://pay?merchant=xxx
        final merchantId = uri.queryParameters['merchant'];
        if (merchantId != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Merchant found: $merchantId')),
          );
          context.pushReplacement(RouteNames.sendPayment);
          return;
        }
      }
    }

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Invalid QR code')),
    );
    setState(() => _scanned = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Scan QR Code'),
      body: MobileScanner(onDetect: _onDetect),
    );
  }
}
