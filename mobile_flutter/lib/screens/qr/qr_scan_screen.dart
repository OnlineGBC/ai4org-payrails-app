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
    // Parse payrails://pay?merchant=xxx
    final uri = Uri.tryParse(data);
    final merchantId = uri?.queryParameters['merchant'];

    if (merchantId != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Merchant found: $merchantId')),
      );
      context.pushReplacement(RouteNames.sendPayment);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Invalid QR code')),
      );
      setState(() => _scanned = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Scan QR Code'),
      body: MobileScanner(onDetect: _onDetect),
    );
  }
}
