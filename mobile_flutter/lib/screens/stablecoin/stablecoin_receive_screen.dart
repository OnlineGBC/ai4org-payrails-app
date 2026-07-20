import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../../models/stablecoin.dart';
import '../../providers/stablecoin_provider.dart';
import '../../services/stablecoin_service.dart';
import '../../widgets/payrails_app_bar.dart';

const _assets = ['USDC', 'USD1'];

class StablecoinReceiveScreen extends ConsumerStatefulWidget {
  const StablecoinReceiveScreen({super.key});

  @override
  ConsumerState<StablecoinReceiveScreen> createState() =>
      _StablecoinReceiveScreenState();
}

class _StablecoinReceiveScreenState
    extends ConsumerState<StablecoinReceiveScreen> {
  String _asset = 'USDC';
  bool _loading = false;
  String? _error;
  CryptoAccount? _account;

  Future<void> _getAddress() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final account = await ref
          .read(stablecoinServiceProvider)
          .createAccount(_asset, 'ethereum');
      setState(() => _account = account);
    } catch (e) {
      setState(() => _error = stablecoinErrorMessage(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final address = _account?.depositAddress;
    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Receive Stablecoin'),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Get a deposit address to receive stablecoin from an '
              'external wallet.',
              style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            initialValue: _asset,
            decoration: const InputDecoration(
              labelText: 'Asset',
              border: OutlineInputBorder(),
            ),
            items: _assets
                .map((a) => DropdownMenuItem(value: a, child: Text(a)))
                .toList(),
            onChanged: (v) => setState(() {
              _asset = v ?? 'USDC';
              _account = null;
            }),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _loading ? null : _getAddress,
              child: _loading
                  ? const SizedBox(
                      height: 18,
                      width: 18,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('Get deposit address'),
            ),
          ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(_error!,
                  style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                      fontSize: 12)),
            ),
          if (address != null) ...[
            const SizedBox(height: 24),
            Center(
              child: QrImageView(
                data: address,
                size: 200,
                backgroundColor: Colors.white,
              ),
            ),
            const SizedBox(height: 16),
            Card(
              child: ListTile(
                title: Text('$_asset · ethereum',
                    style: Theme.of(context).textTheme.bodySmall),
                subtitle: Text(address),
                trailing: IconButton(
                  icon: const Icon(Icons.copy),
                  tooltip: 'Copy address',
                  onPressed: () {
                    Clipboard.setData(ClipboardData(text: address));
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Address copied')),
                    );
                  },
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
