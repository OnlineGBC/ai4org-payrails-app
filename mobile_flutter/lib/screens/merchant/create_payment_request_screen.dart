import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/auth_provider.dart';
import '../../providers/consumer_provider.dart';
import '../../router/route_names.dart';
import '../../widgets/payrails_app_bar.dart';

class CreatePaymentRequestScreen extends ConsumerStatefulWidget {
  const CreatePaymentRequestScreen({super.key});

  @override
  ConsumerState<CreatePaymentRequestScreen> createState() =>
      _CreatePaymentRequestScreenState();
}

class _CreatePaymentRequestScreenState
    extends ConsumerState<CreatePaymentRequestScreen> {
  final _amountController = TextEditingController();
  final _descriptionController = TextEditingController();
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _amountController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _createRequest() async {
    final amount = double.tryParse(_amountController.text);
    if (amount == null || amount <= 0) {
      setState(() => _error = 'Enter a valid amount');
      return;
    }

    final user = ref.read(authStateProvider).user;
    if (user?.merchantId == null) {
      setState(() => _error = 'No merchant ID found');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final service = ref.read(consumerServiceProvider);
      final description = _descriptionController.text.trim().isEmpty
          ? null
          : _descriptionController.text.trim();
      final request = await service.createPaymentRequest(
        user!.merchantId!,
        amount,
        description,
      );

      if (mounted) {
        context.push(
          '${RouteNames.merchantPaymentRequestQr}'
          '?requestId=${request.id}'
          '&amount=${request.amount.toStringAsFixed(2)}'
          '&description=${Uri.encodeComponent(request.description ?? '')}',
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _loading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Request Payment'),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _amountController,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
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
            const SizedBox(height: 24),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Text(
                  _error!,
                  style:
                      TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ),
            ElevatedButton(
              onPressed: _loading ? null : _createRequest,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: _loading
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Generate QR Code',
                      style: TextStyle(fontSize: 16)),
            ),
          ],
        ),
      ),
    );
  }
}
