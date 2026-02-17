import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/auth_provider.dart';
import '../../providers/payment_provider.dart';
import '../../widgets/payrails_app_bar.dart';
import '../../widgets/amount_input.dart';

class SendPaymentScreen extends ConsumerStatefulWidget {
  const SendPaymentScreen({super.key});

  @override
  ConsumerState<SendPaymentScreen> createState() => _SendPaymentScreenState();
}

class _SendPaymentScreenState extends ConsumerState<SendPaymentScreen> {
  final _formKey = GlobalKey<FormState>();
  final _amountController = TextEditingController();
  final _receiverController = TextEditingController();
  String? _selectedRail;
  bool _isLoading = false;
  String? _error;

  @override
  void dispose() {
    _amountController.dispose();
    _receiverController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    final user = ref.read(authStateProvider).user;
    if (user?.merchantId == null) {
      setState(() => _error = 'No merchant associated with your account');
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final service = ref.read(paymentServiceProvider);
      final txn = await service.sendPayment(
        senderMerchantId: user!.merchantId!,
        receiverMerchantId: _receiverController.text.trim(),
        amount: double.parse(_amountController.text),
        idempotencyKey: DateTime.now().millisecondsSinceEpoch.toString(),
        preferredRail: _selectedRail,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Payment ${txn.status} via ${txn.rail}'),
            backgroundColor:
                txn.status == 'completed' ? Colors.green : Colors.orange,
          ),
        );
        context.pop();
      }
    } catch (e) {
      setState(() => _error = 'Payment failed: $e');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Send Payment'),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 500),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (_error != null)
                  Container(
                    padding: const EdgeInsets.all(12),
                    margin: const EdgeInsets.only(bottom: 16),
                    decoration: BoxDecoration(
                      color: Colors.red.shade50,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(_error!, style: TextStyle(color: Colors.red.shade700)),
                  ),
                TextFormField(
                  controller: _receiverController,
                  decoration: const InputDecoration(
                    labelText: 'Receiver Merchant ID',
                    prefixIcon: Icon(Icons.business),
                  ),
                  validator: (v) =>
                      v == null || v.isEmpty ? 'Receiver is required' : null,
                ),
                const SizedBox(height: 16),
                AmountInput(controller: _amountController),
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  initialValue: _selectedRail,
                  decoration: const InputDecoration(
                    labelText: 'Preferred Rail (optional)',
                    prefixIcon: Icon(Icons.route),
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
                const SizedBox(height: 32),
                ElevatedButton(
                  onPressed: _isLoading ? null : _submit,
                  child: _isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Send Payment'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
