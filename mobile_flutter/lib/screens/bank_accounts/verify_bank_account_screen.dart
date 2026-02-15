import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/merchant_provider.dart';
import '../../widgets/payrails_app_bar.dart';

class VerifyBankAccountScreen extends ConsumerStatefulWidget {
  final String merchantId;
  final String accountId;
  final String amount1;
  final String amount2;

  const VerifyBankAccountScreen({
    super.key,
    required this.merchantId,
    required this.accountId,
    this.amount1 = '',
    this.amount2 = '',
  });

  @override
  ConsumerState<VerifyBankAccountScreen> createState() =>
      _VerifyBankAccountScreenState();
}

class _VerifyBankAccountScreenState
    extends ConsumerState<VerifyBankAccountScreen> {
  final _formKey = GlobalKey<FormState>();
  final _amount1Controller = TextEditingController();
  final _amount2Controller = TextEditingController();
  bool _isLoading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _amount1Controller.text = widget.amount1;
    _amount2Controller.text = widget.amount2;
  }

  String _extractError(Object e) {
    if (e is DioException && e.response?.data is Map) {
      final detail = e.response!.data['detail'];
      if (detail != null) return detail.toString();
    }
    return e.toString();
  }

  @override
  void dispose() {
    _amount1Controller.dispose();
    _amount2Controller.dispose();
    super.dispose();
  }

  Future<void> _verifyMicroDeposits() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final service = ref.read(merchantServiceProvider);
      await service.verifyMicroDeposits(
        widget.merchantId,
        widget.accountId,
        amount1: _amount1Controller.text.trim(),
        amount2: _amount2Controller.text.trim(),
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Bank account verified')),
        );
        context.pop();
      }
    } catch (e) {
      setState(() => _error = _extractError(e));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _verifyInstant() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final service = ref.read(merchantServiceProvider);
      await service.verifyInstant(widget.merchantId, widget.accountId);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Bank account verified')),
        );
        context.pop();
      }
    } catch (e) {
      setState(() => _error = _extractError(e));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Verify Bank Account'),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
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
                child:
                    Text(_error!, style: TextStyle(color: Colors.red.shade700)),
              ),
            Text(
              'Option A — Micro-Deposit Verification',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            const Text(
              'Enter the two small deposit amounts that appeared in your bank account.',
            ),
            const SizedBox(height: 16),
            Form(
              key: _formKey,
              child: Column(
                children: [
                  TextFormField(
                    controller: _amount1Controller,
                    decoration: const InputDecoration(
                      labelText: 'Amount 1',
                      hintText: '0.32',
                      prefixIcon: Icon(Icons.attach_money),
                    ),
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    validator: (v) {
                      if (v == null || v.trim().isEmpty) {
                        return 'Required';
                      }
                      if (double.tryParse(v.trim()) == null) {
                        return 'Enter a valid amount';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _amount2Controller,
                    decoration: const InputDecoration(
                      labelText: 'Amount 2',
                      hintText: '0.45',
                      prefixIcon: Icon(Icons.attach_money),
                    ),
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    validator: (v) {
                      if (v == null || v.trim().isEmpty) {
                        return 'Required';
                      }
                      if (double.tryParse(v.trim()) == null) {
                        return 'Enter a valid amount';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: _isLoading ? null : _verifyMicroDeposits,
                    child: _isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('Verify Deposits'),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),
            const Divider(),
            const SizedBox(height: 32),
            Text(
              'Option B — Instant Verification',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            const Text(
              'Instantly verify your bank account without waiting for micro-deposits.',
            ),
            const SizedBox(height: 16),
            OutlinedButton(
              onPressed: _isLoading ? null : _verifyInstant,
              child: _isLoading
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Verify Instantly'),
            ),
          ],
        ),
      ),
    );
  }
}
