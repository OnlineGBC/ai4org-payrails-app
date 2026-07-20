import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/stablecoin_provider.dart';
import '../../services/stablecoin_service.dart';
import '../../widgets/payrails_app_bar.dart';

const _assets = ['USDC', 'USD1'];

class StablecoinSendScreen extends ConsumerStatefulWidget {
  const StablecoinSendScreen({super.key});

  @override
  ConsumerState<StablecoinSendScreen> createState() =>
      _StablecoinSendScreenState();
}

class _StablecoinSendScreenState extends ConsumerState<StablecoinSendScreen> {
  final _addressController = TextEditingController();
  final _amountController = TextEditingController();
  String _asset = 'USDC';
  bool _submitting = false;
  String? _error;

  @override
  void dispose() {
    _addressController.dispose();
    _amountController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final address = _addressController.text.trim();
    final amount = double.tryParse(_amountController.text.trim());
    if (address.isEmpty) {
      setState(() => _error = 'Enter a destination address.');
      return;
    }
    if (amount == null || amount <= 0) {
      setState(() => _error = 'Enter a valid amount.');
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      await ref
          .read(stablecoinServiceProvider)
          .send(address, amount, _asset, 'ethereum');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Sent $amount $_asset')),
        );
        context.pop();
      }
    } catch (e) {
      // 403 => sanctions/KYT screening block; message comes from the API detail.
      if (mounted) setState(() => _error = stablecoinErrorMessage(e));
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Send Stablecoin'),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Send stablecoin on-chain to an external address. The '
              'destination is screened before any funds move.',
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
            onChanged: (v) => setState(() => _asset = v ?? 'USDC'),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _addressController,
            decoration: const InputDecoration(
              labelText: 'Destination address',
              hintText: '0x…',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _amountController,
            keyboardType:
                const TextInputType.numberWithOptions(decimal: true),
            inputFormatters: [
              FilteringTextInputFormatter.allow(RegExp(r'^\d+\.?\d{0,6}')),
            ],
            decoration: InputDecoration(
              labelText: 'Amount ($_asset)',
              border: const OutlineInputBorder(),
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
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _submitting ? null : _submit,
              child: _submitting
                  ? const SizedBox(
                      height: 18,
                      width: 18,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('Send'),
            ),
          ),
        ],
      ),
    );
  }
}
