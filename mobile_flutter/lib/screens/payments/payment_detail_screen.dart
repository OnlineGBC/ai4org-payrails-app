import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../models/transaction.dart';
import '../../providers/payment_provider.dart';
import '../../widgets/payrails_app_bar.dart';
import '../../widgets/status_chip.dart';
import '../../widgets/rail_badge.dart';

class PaymentDetailScreen extends ConsumerStatefulWidget {
  final String paymentId;

  const PaymentDetailScreen({super.key, required this.paymentId});

  @override
  ConsumerState<PaymentDetailScreen> createState() => _PaymentDetailScreenState();
}

class _PaymentDetailScreenState extends ConsumerState<PaymentDetailScreen> {
  Transaction? _transaction;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final service = ref.read(paymentServiceProvider);
      final txn = await service.getPayment(widget.paymentId);
      setState(() {
        _transaction = txn;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Payment Details'),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text('Error: $_error'))
              : _buildDetail(),
    );
  }

  Widget _buildDetail() {
    final txn = _transaction!;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Amount
          Center(
            child: Text(
              '\$${txn.amount.toStringAsFixed(2)}',
              style: Theme.of(context)
                  .textTheme
                  .headlineLarge
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(height: 8),
          Center(child: StatusChip(status: txn.status)),
          const SizedBox(height: 24),

          // Status timeline
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Status Timeline',
                      style: Theme.of(context).textTheme.titleSmall),
                  const SizedBox(height: 12),
                  _timelineStep('Created', true),
                  _timelineStep('Processing',
                      txn.status != 'pending'),
                  _timelineStep(
                      'Completed', txn.status == 'completed'),
                  if (txn.status == 'failed')
                    _timelineStep('Failed', true, isError: true),
                  if (txn.status == 'cancelled')
                    _timelineStep('Cancelled', true, isError: true),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Details
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  _detailRow('Transaction ID', txn.id),
                  _detailRow('Sender', txn.senderMerchantId),
                  _detailRow('Receiver', txn.receiverMerchantId),
                  _detailRow('Rail', ''),
                  if (txn.rail != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.end,
                        children: [RailBadge(rail: txn.rail)],
                      ),
                    ),
                  if (txn.referenceId != null)
                    _detailRow('Reference', txn.referenceId!),
                  if (txn.failureReason != null)
                    _detailRow('Failure Reason', txn.failureReason!),
                  if (txn.createdAt != null)
                    _detailRow('Created', txn.createdAt.toString()),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _detailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(label,
                style: const TextStyle(
                    color: Colors.grey, fontWeight: FontWeight.w500)),
          ),
          Expanded(
            child: Text(value, style: const TextStyle(fontWeight: FontWeight.w500)),
          ),
        ],
      ),
    );
  }

  Widget _timelineStep(String label, bool active, {bool isError = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(
            active
                ? (isError ? Icons.cancel : Icons.check_circle)
                : Icons.radio_button_unchecked,
            color: active
                ? (isError ? Colors.red : Colors.green)
                : Colors.grey.shade300,
            size: 20,
          ),
          const SizedBox(width: 12),
          Text(label,
              style: TextStyle(
                color: active ? Colors.black87 : Colors.grey,
                fontWeight: active ? FontWeight.w500 : FontWeight.normal,
              )),
        ],
      ),
    );
  }
}
