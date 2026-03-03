import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/consumer_provider.dart';
import '../../router/route_names.dart';
import '../../utils/anomaly_detection.dart';
import '../../widgets/payrails_app_bar.dart';

// Default descriptions by merchant category — used to pre-populate the field
String _defaultDescription(String merchantName) {
  final lower = merchantName.toLowerCase().replaceAll(' ', '');
  if (lower.contains('westernunion')) return 'Money transfer';
  if (lower.contains('netflix')) return 'Monthly streaming subscription';
  if (lower.contains('boostmobile')) return 'Mobile phone top-up';
  if (lower.contains('walmart') || lower.contains('foodlion') ||
      lower.contains('aldi') || lower.contains('costco') ||
      lower.contains('dollargeneral')) {
    return 'Grocery purchase';
  }
  if (lower.contains('mcdonalds') || lower.contains('burgerking') ||
      lower.contains('subway')) {
    return 'Meal / food order';
  }
  if (lower.contains('target') || lower.contains('nike')) return 'Retail purchase';
  return 'Payment';
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
  // Resolved payment target:
  // - _resolvedMerchantId set   → pay merchant via /consumer/pay
  // - _resolvedUserId set       → wallet-to-wallet via /wallet/send
  String? _resolvedMerchantId;
  String? _resolvedUserId;

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
    final service = ref.read(consumerServiceProvider);

    // Step 1: try the ID as a merchant
    try {
      final info = await service.getMerchantInfo(widget.merchantId);
      final name = info['name'] as String? ?? 'Unknown Merchant';
      setState(() {
        _merchantName = name;
        _resolvedMerchantId = widget.merchantId;
        _loadingMerchant = false;
      });
      if (_descriptionController.text.isEmpty) {
        _descriptionController.text = _defaultDescription(name);
      }
      return;
    } on DioException catch (e) {
      if (e.response?.statusCode != 404) {
        setState(() {
          _error = 'Could not load merchant: ${e.message}';
          _loadingMerchant = false;
        });
        return;
      }
      // 404 — fall through to user lookup
    }

    // Step 2: try the ID as a consumer user
    try {
      final userInfo = await service.getUserInfo(widget.merchantId);
      final email = userInfo['email'] as String? ?? widget.merchantId;
      final linkedMerchantId = userInfo['merchant_id'] as String?;

      if (linkedMerchantId != null && linkedMerchantId.isNotEmpty) {
        // User has a linked merchant — resolve to that merchant
        final mInfo = await service.getMerchantInfo(linkedMerchantId);
        final mName = mInfo['name'] as String? ?? email;
        setState(() {
          _merchantName = mName;
          _resolvedMerchantId = linkedMerchantId;
          _loadingMerchant = false;
        });
        if (_descriptionController.text.isEmpty) {
          _descriptionController.text = _defaultDescription(mName);
        }
      } else {
        // User has no linked merchant — use wallet-to-wallet send
        setState(() {
          _merchantName = email;
          _resolvedUserId = widget.merchantId;
          _loadingMerchant = false;
        });
        if (_descriptionController.text.isEmpty) {
          _descriptionController.text = 'Payment to $email';
        }
      }
    } catch (_) {
      setState(() {
        _error = 'Could not find merchant or user with ID: ${widget.merchantId}';
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

    final desc = _descriptionController.text.trim();
    if (desc.isEmpty) {
      setState(() => _error = 'Description is required');
      return;
    }

    // Anomaly check — always runs
    if (_merchantName != null) {
      final warning = checkAnomaly(_merchantName!, desc);
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
      final Map<String, dynamic> result;
      if (_resolvedUserId != null) {
        // Plain user with no merchant — wallet-to-wallet send
        result = await service.sendToWallet(
          _resolvedUserId!,
          amount,
          description: desc.isEmpty ? null : desc,
        );
      } else {
        // Merchant payment (direct or via linked merchant)
        result = await service.consumerPay(
          _resolvedMerchantId ?? widget.merchantId,
          amount,
          description: desc.isEmpty ? null : desc,
          preferredRail: _selectedRail,
        );
      }
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
                      Icon(
                        _resolvedUserId != null ? Icons.person : Icons.store,
                        size: 64,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                      const SizedBox(height: 16),
                      Text(
                        _merchantName ?? 'Merchant',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _resolvedUserId != null
                            ? 'User: ${widget.merchantId}'
                            : 'Merchant: ${_resolvedMerchantId ?? widget.merchantId}',
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
                          labelText: 'Description (Required)',
                          hintText: 'What is this payment for?',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 16),
                      DropdownButtonFormField<String>(
                        initialValue: _selectedRail,
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
