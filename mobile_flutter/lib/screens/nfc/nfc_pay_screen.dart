import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:nfc_manager/nfc_manager.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/payrails_app_bar.dart';

class NfcPayScreen extends ConsumerStatefulWidget {
  const NfcPayScreen({super.key});

  @override
  ConsumerState<NfcPayScreen> createState() => _NfcPayScreenState();
}

class _NfcPayScreenState extends ConsumerState<NfcPayScreen> {
  bool _isAvailable = false;
  bool _isScanning = false;
  String _statusMessage = 'Checking NFC availability...';

  @override
  void initState() {
    super.initState();
    _checkNfc();
  }

  Future<void> _checkNfc() async {
    try {
      final availability = await NfcManager.instance.checkAvailability();
      final available = availability == NfcAvailability.enabled;
      setState(() {
        _isAvailable = available;
        _statusMessage =
            available ? 'Tap to start NFC payment' : 'NFC is not available on this device';
      });
    } catch (e) {
      setState(() => _statusMessage = 'NFC check failed: $e');
    }
  }

  Future<void> _startSession() async {
    if (!_isAvailable) return;

    setState(() {
      _isScanning = true;
      _statusMessage = 'Hold device near NFC tag...';
    });

    NfcManager.instance.startSession(
      pollingOptions: {NfcPollingOption.iso14443},
      onDiscovered: (NfcTag tag) async {
        final user = ref.read(authStateProvider).user;
        setState(() {
          _statusMessage =
              'Tag detected! Merchant: ${user?.merchantId ?? "unknown"}';
          _isScanning = false;
        });
        await NfcManager.instance.stopSession();
      },
    );
  }

  @override
  void dispose() {
    if (_isScanning) {
      NfcManager.instance.stopSession();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const PayRailsAppBar(title: 'NFC Payment'),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.nfc,
                size: 100,
                color: _isAvailable
                    ? Theme.of(context).colorScheme.primary
                    : Colors.grey,
              ),
              const SizedBox(height: 24),
              Text(
                _statusMessage,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 32),
              if (_isAvailable && !_isScanning)
                ElevatedButton.icon(
                  onPressed: _startSession,
                  icon: const Icon(Icons.contactless),
                  label: const Text('Start NFC Scan'),
                ),
              if (_isScanning) const CircularProgressIndicator(),
            ],
          ),
        ),
      ),
    );
  }
}
