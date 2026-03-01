import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/consumer_provider.dart';
import '../../router/route_names.dart';
import '../../widgets/payrails_app_bar.dart';

// Anomaly detection: map of merchant name substrings (lowercase) to category
const Map<String, String> _merchantCategory = {
  'westernunion': 'money_transfer',
  'netflix': 'streaming',
  'boostmobile': 'telecom',
  'foodlion': 'grocery',
  'aldi': 'grocery',
  'costco': 'grocery',
  'walmart': 'grocery',
  'dollargeneral': 'grocery',
  'mcdonalds': 'restaurant',
  'burgerking': 'restaurant',
  'subway': 'restaurant',
  'target': 'retail',
  'nike': 'retail',
};

const Set<String> _physicalGoodsKeywords = {
  'toothpaste', 'groceries', 'grocery', 'shoes', 'burger', 'sandwich',
  'meal', 'food', 'clothing', 'clothes', 'shirt', 'pants', 'dress',
  'hardware', 'furniture', 'electronics', 'appliance',
};

const Set<String> _financialKeywords = {
  'transfer', 'remittance', 'wire', 'send money', 'money order',
  'cash', 'loan', 'payment plan', 'investment',
};

String? _checkAnomaly(String merchantName, String description) {
  final merchantLower = merchantName.toLowerCase().replaceAll(' ', '');
  final descLower = description.toLowerCase();

  String? category;
  for (final entry in _merchantCategory.entries) {
    if (merchantLower.contains(entry.key)) {
      category = entry.value;
      break;
    }
  }
  if (category == null) return null;

  if (category == 'money_transfer') {
    for (final kw in _physicalGoodsKeywords) {
      if (descLower.contains(kw)) {
        return 'Unusual description for a money transfer merchant. '
            '"$description" sounds like a physical purchase. '
            'Proceed only if this is intentional.';
      }
    }
  }

  if (category == 'streaming' || category == 'telecom') {
    for (final kw in _physicalGoodsKeywords) {
      if (descLower.contains(kw)) {
        return 'Unusual description for a ${category == 'streaming' ? 'streaming' : 'telecom'} merchant. '
            '"$description" sounds like a physical purchase. '
            'Proceed only if this is intentional.';
      }
    }
  }

  if (category == 'restaurant' || category == 'grocery' || category == 'retail') {
    for (final kw in _financialKeywords) {
      if (descLower.contains(kw)) {
        return 'Unusual description for a ${category} merchant. '
            '"$description" sounds like a financial transaction. '
            'Proceed only if this is intentional.';
      }
    }
  }

  return null;
}

class ConsumerPayConfirmScreen extends ConsumerStatefulWidget {
  final String merchantId;

  const ConsumerPayConfirmScreen({super.key, required this.merchantId});

  @override
  ConsumerState<ConsumerPayConfirmScreen> createState() =>
      _ConsumerPayConfirmScreenState();
}

class _ConsumerPayConfirmScreenState
    extends ConsumerState<ConsumerPayConfirmScreen> {
  final _amountController = TextEditingController();
  final _descriptionController = TextEditingController();
  String? _merchantName;
  String? _selectedRail;
  bool _loadingMerchant = true;
  bool _paying = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadMerchant();
  }

  @override
  void dispose() {
    _amountController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _loadMerchant() async {
    try {
      final service = ref.read(consumerServiceProvider);
      final info = await service.getMerchantInfo(widget.merchantId);
      setState(() {
        _merchantName = info['name'] as String? ?? 'Unknown Merchant';
        _loadingMerchant = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Could not find merchant: ${e.toString()}';
        _loadingMerchant = false;
      });
    }
  }

  Future<void> _confirmPay() async {
    final amount = double.tryParse(_amountController.text);
    if (amount == null || amount <= 0) {
      setState(() => _error = 'Enter a valid amount');
      return;
    }

    // Anomaly check
    final desc = _descriptionController.text.trim();
    if (desc.isNotEmpty && _merchantName != null) {
      final warning = _checkAnomaly(_merchantName!, desc);
      if (warning != null) {
        final proceed = await _showAnomalyDialog(warning);
        if (!proceed) return;
      }
    }

    setState(() {
      _paying = true;
      _error = null;
    });

    try {
      final service = ref.read(consumerServiceProvider);
      final description = desc.isEmpty ? null : desc;
      final result = await service.consumerPay(
        widget.merchantId,
        amount,
        description: description,
        preferredRail: _selectedRail,
      );
      final status = result['status'] as String?;

      if (mounted) {
        if (status == 'completed') {
          ref.read(walletBalanceProvider.notifier).load();
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Payment successful!')),
          );
          context.go(RouteNames.consumerDashboard);
        } else {
          setState(() {
            _error = result['failure_reason'] as String? ??
                'Payment failed (status: $status)';
            _paying = false;
          });
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _paying = false;
        });
      }
    }
  }

  Future<bool> _showAnomalyDialog(String warning) async {
    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Unusual Transaction Detected'),
        content: Text(warning),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Proceed Anyway'),
          ),
        ],
      ),
    );
    return result ?? false;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Pay Merchant'),
      body: _loadingMerchant
          ? const Center(child: CircularProgressIndicator())
          : _merchantName == null && _error != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(32),
                    child: Text(_error!, textAlign: TextAlign.center),
                  ),
                )
              : Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      const SizedBox(height: 16),
                      Icon(Icons.store,
                          size: 64,
                          color: Theme.of(context).colorScheme.primary),
                      const SizedBox(height: 16),
                      Text(
                        _merchantName ?? 'Merchant',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'ID: ${widget.merchantId}',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              fontFamily: 'monospace',
                            ),
                      ),
                      const SizedBox(height: 32),
                      TextField(
                        controller: _amountController,
                        keyboardType: const TextInputType.numberWithOptions(
                            decimal: true),
                        decoration: const InputDecoration(
                          labelText: 'Amount',
                          prefixText: '\$ ',
                          border: OutlineInputBorder(),
                        ),
                        autofocus: true,
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        controller: _descriptionController,
                        decoration: const InputDecoration(
                          labelText: 'Description (optional)',
                          hintText: 'e.g. Coffee order',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 16),
                      DropdownButtonFormField<String>(
                        value: _selectedRail,
                        decoration: const InputDecoration(
                          labelText: 'Preferred Rail (optional)',
                          prefixIcon: Icon(Icons.route),
                          border: OutlineInputBorder(),
                        ),
                        items: const [
                          DropdownMenuItem(value: null, child: Text('Auto-select')),
                          DropdownMenuItem(value: 'fednow', child: Text('FedNow (1.25% discount)')),
                          DropdownMenuItem(value: 'rtp', child: Text('RTP (1.25% discount)')),
                          DropdownMenuItem(value: 'ach', child: Text('ACH')),
                          DropdownMenuItem(value: 'card', child: Text('Card')),
                        ],
                        onChanged: (v) => setState(() => _selectedRail = v),
                      ),
                      const Spacer(),
                      if (_error != null)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 16),
                          child: Text(
                            _error!,
                            style: TextStyle(
                                color: Theme.of(context).colorScheme.error),
                            textAlign: TextAlign.center,
                          ),
                        ),
                      // Disclaimer
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 10),
                        margin: const EdgeInsets.only(bottom: 12),
                        decoration: BoxDecoration(
                          color: Colors.amber.shade50,
                          border: Border.all(color: Colors.amber.shade300),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Text(
                          '⚠️  MVP Demo Environment — All transactions are simulated.\n'
                          'Do not enter real personal or financial information.',
                          style: TextStyle(fontSize: 12),
                          textAlign: TextAlign.center,
                        ),
                      ),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: _paying ? null : _confirmPay,
                          style: ElevatedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 16),
                          ),
                          child: _paying
                              ? const SizedBox(
                                  height: 20,
                                  width: 20,
                                  child: CircularProgressIndicator(
                                      strokeWidth: 2),
                                )
                              : const Text('Confirm Payment',
                                  style: TextStyle(fontSize: 18)),
                        ),
                      ),
                      const SizedBox(height: 16),
                      TextButton(
                        onPressed: () => context.pop(),
                        child: const Text('Cancel'),
                      ),
                    ],
                  ),
                ),
    );
  }
}
