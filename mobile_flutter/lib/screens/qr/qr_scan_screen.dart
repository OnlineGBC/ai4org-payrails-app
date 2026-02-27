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
  String? _scannedId;

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

    String? merchantId;
    if (uri != null && uri.scheme == 'payrails' && uri.host == 'pay') {
      merchantId = uri.queryParameters['merchant'];
    }
    merchantId ??= data.trim().isNotEmpty ? data.trim() : null;

    if (merchantId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Invalid QR code or Merchant ID')),
      );
      setState(() => _scanned = false);
      return;
    }

    setState(() => _scannedId = merchantId);
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

  void _cancelScan() {
    setState(() {
      _scannedId = null;
      _scanned = false;
    });
  }

  // Venmo-style inline confirmation panel — overlaid on the camera
  Widget _buildConfirmationPanel(String merchantId) {
    return Positioned(
      left: 0,
      right: 0,
      bottom: 0,
      child: Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          boxShadow: [
            BoxShadow(color: Colors.black26, blurRadius: 16, offset: Offset(0, -4)),
          ],
        ),
        padding: const EdgeInsets.fromLTRB(24, 20, 24, 36),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Drag handle
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey[300],
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                const Icon(Icons.qr_code_scanner, color: Colors.blue, size: 28),
                const SizedBox(width: 12),
                const Text('QR Code Scanned',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 16),
            const Text('Merchant ID', style: TextStyle(color: Colors.grey, fontSize: 13)),
            const SizedBox(height: 4),
            Text(
              merchantId,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                fontFamily: 'monospace',
              ),
            ),
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: _cancelScan,
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                    child: const Text('Cancel'),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: ElevatedButton(
                    onPressed: () => _navigateToPayConfirm(merchantId),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                    child: const Text('Proceed to Pay'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
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
          // Inline confirmation for manual entry
          if (_scannedId != null) ...[
            const SizedBox(height: 32),
            const Divider(),
            const SizedBox(height: 16),
            const Text('Confirm Merchant ID',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text(_scannedId!,
                style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    fontFamily: 'monospace')),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: _cancelScan,
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                    child: const Text('Cancel'),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: ElevatedButton(
                    onPressed: () => _navigateToPayConfirm(_scannedId!),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                    child: const Text('Proceed to Pay'),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final showManualEntry = _cameraError;

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
                // Show confirmation panel when QR is scanned
                if (_scannedId != null)
                  _buildConfirmationPanel(_scannedId!)
                else
                  Positioned(
                    bottom: 24,
                    left: 24,
                    right: 24,
                    child: ElevatedButton.icon(
                      onPressed: () => setState(() => _cameraError = true),
                      icon: const Icon(Icons.keyboard),
                      label: const Text(
                        'Enter Merchant ID manually instead',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: Colors.blue,
                        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
                        elevation: 6,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                    ),
                  ),
              ],
            ),
    );
  }
}
