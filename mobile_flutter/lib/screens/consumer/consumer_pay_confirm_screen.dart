import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../models/payment_request.dart';
import '../../providers/consumer_provider.dart';
import '../../router/route_names.dart';
import '../../widgets/payrails_app_bar.dart';

class ConsumerPayConfirmScreen extends ConsumerStatefulWidget {
  final String requestId;

  const ConsumerPayConfirmScreen({super.key, required this.requestId});

  @override
  ConsumerState<ConsumerPayConfirmScreen> createState() =>
      _ConsumerPayConfirmScreenState();
}

class _ConsumerPayConfirmScreenState
    extends ConsumerState<ConsumerPayConfirmScreen> {
  PaymentRequest? _request;
  bool _loading = true;
  bool _paying = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadRequest();
  }

  Future<void> _loadRequest() async {
    try {
      final service = ref.read(consumerServiceProvider);
      final req = await service.getPaymentRequest(widget.requestId);
      setState(() {
        _request = req;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  Future<void> _confirmPay() async {
    if (_request == null || _paying) return;
    setState(() {
      _paying = true;
      _error = null;
    });

    try {
      final service = ref.read(consumerServiceProvider);
      final result = await service.consumerPay(_request!.id);
      final status = result['status'] as String?;

      if (mounted) {
        if (status == 'completed') {
          // Refresh wallet balance
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Confirm Payment'),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _request == null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(32),
                    child: Text(_error ?? 'Payment request not found',
                        textAlign: TextAlign.center),
                  ),
                )
              : Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      const SizedBox(height: 32),
                      Icon(Icons.store,
                          size: 64,
                          color: Theme.of(context).colorScheme.primary),
                      const SizedBox(height: 16),
                      Text(
                        _request!.merchantName ?? 'Merchant',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 8),
                      if (_request!.description != null)
                        Text(
                          _request!.description!,
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      const SizedBox(height: 32),
                      Text(
                        '\$${_request!.amount.toStringAsFixed(2)}',
                        style: Theme.of(context)
                            .textTheme
                            .displaySmall
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 8),
                      Text(_request!.currency,
                          style: Theme.of(context).textTheme.bodySmall),
                      if (_request!.status != 'pending') ...[
                        const SizedBox(height: 16),
                        Chip(
                          label: Text(
                              'Status: ${_request!.status.toUpperCase()}'),
                          backgroundColor:
                              Theme.of(context).colorScheme.errorContainer,
                        ),
                      ],
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
                      if (_request!.status == 'pending')
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton(
                            onPressed: _paying ? null : _confirmPay,
                            style: ElevatedButton.styleFrom(
                              padding:
                                  const EdgeInsets.symmetric(vertical: 16),
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
