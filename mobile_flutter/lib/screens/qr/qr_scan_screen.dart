import 'package:flutter/foundation.dart' show kIsWeb;
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
  final _manualController = TextEditingController();
  bool _cameraError = false;

  @override
  void dispose() {
    _manualController.dispose();
    super.dispose();
  }

  void _navigateToPayConfirm(String merchantId) {
    context.push(
      '${RouteNames.consumerPayConfirm}?merchantId=$merchantId',
    );
  }

  void _handleQrData(String data) {
    final uri = Uri.tryParse(data);

    if (uri != null && uri.scheme == 'payrails' && uri.host == 'pay') {
      final merchantId = uri.queryParameters['merchant'];
      if (merchantId != null) {
        _navigateToPayConfirm(merchantId);
        return;
      }
    }

    // Also accept a bare merchant ID (UUID)
    final uuidPattern = RegExp(
      r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$',
    );
    if (uuidPattern.hasMatch(data.trim())) {
      _navigateToPayConfirm(data.trim());
      return;
    }

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Invalid QR code or Merchant ID')),
    );
    setState(() => _scanned = false);
  }

  void _onDetect(BarcodeCapture capture) {
    if (_scanned) return;
    final barcode = capture.barcodes.firstOrNull;
    if (barcode?.rawValue == null) return;

    setState(() => _scanned = true);
    _handleQrData(barcode!.rawValue!);
  }

  void _submitManualId() {
    final text = _manualController.text.trim();
    if (text.isEmpty) return;
    _handleQrData(text);
  }

  Widget _buildManualEntry() {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.videocam_off, size: 64,
              color: Theme.of(context).colorScheme.outline),
          const SizedBox(height: 16),
          Text(
            'Camera is not available.\n'
            'On web, camera requires HTTPS.\n'
            'You can enter the Merchant ID manually.',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyLarge,
          ),
          const SizedBox(height: 24),
          TextField(
            controller: _manualController,
            decoration: const InputDecoration(
              labelText: 'Merchant ID',
              hintText: 'Paste the Merchant ID',
              border: OutlineInputBorder(),
            ),
            onSubmitted: (_) => _submitManualId(),
          ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: _submitManualId,
            icon: const Icon(Icons.send),
            label: const Text('Submit'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 24),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final showManualEntry = kIsWeb || _cameraError;

    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Scan QR Code'),
      body: showManualEntry
          ? _buildManualEntry()
          : Stack(
              children: [
                MobileScanner(
                  onDetect: _onDetect,
                  errorBuilder: (context, error, child) {
                    WidgetsBinding.instance.addPostFrameCallback((_) {
                      if (mounted && !_cameraError) {
                        setState(() => _cameraError = true);
                      }
                    });
                    return const SizedBox.shrink();
                  },
                ),
                Positioned(
                  bottom: 24,
                  left: 24,
                  right: 24,
                  child: TextButton(
                    onPressed: () => setState(() => _cameraError = true),
                    child: const Text('Enter Merchant ID manually instead'),
                  ),
                ),
              ],
            ),
    );
  }
}
