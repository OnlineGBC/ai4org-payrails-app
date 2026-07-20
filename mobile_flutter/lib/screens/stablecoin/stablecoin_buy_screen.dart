import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/stablecoin_provider.dart';
import '../../services/stablecoin_service.dart';
import '../../widgets/payrails_app_bar.dart';

const _assets = ['USDC', 'USD1'];

class StablecoinBuyScreen extends ConsumerStatefulWidget {
  const StablecoinBuyScreen({super.key});

  @override
  ConsumerState<StablecoinBuyScreen> createState() =>
      _StablecoinBuyScreenState();
}

class _StablecoinBuyScreenState extends ConsumerState<StablecoinBuyScreen> {
  final _amountController = TextEditingController();
  String _asset = 'USDC';
  bool _submitting = false;
  String? _error;

  @override
  void dispose() {
    _amountController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final usd = double.tryParse(_amountController.text.trim());
    if (usd == null || usd <= 0) {
      setState(() => _error = 'Enter a valid USD amount.');
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      await ref.read(stablecoinServiceProvider).onramp(usd, _asset, 'ethereum');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Bought $_asset with \$$usd')),
        );
        context.pop();
      }
    } catch (e) {
      if (mounted) setState(() => _error = stablecoinErrorMessage(e));
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Buy Stablecoin'),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Convert USD from your wallet into a stablecoin.',
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
            controller: _amountController,
            keyboardType:
                const TextInputType.numberWithOptions(decimal: true),
            inputFormatters: [
              FilteringTextInputFormatter.allow(RegExp(r'^\d+\.?\d{0,2}')),
            ],
            decoration: const InputDecoration(
              labelText: 'USD amount',
              prefixText: '\$ ',
              border: OutlineInputBorder(),
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
                  : const Text('Buy'),
            ),
          ),
        ],
      ),
    );
  }
}
