import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../models/merchant.dart';
import '../../providers/auth_provider.dart';
import '../../providers/merchant_provider.dart';
import '../../router/route_names.dart';
import '../../widgets/payrails_app_bar.dart';
import '../../widgets/status_chip.dart';

class MerchantScreen extends ConsumerStatefulWidget {
  const MerchantScreen({super.key});

  @override
  ConsumerState<MerchantScreen> createState() => _MerchantScreenState();
}

class _MerchantScreenState extends ConsumerState<MerchantScreen> {
  final _einController = TextEditingController();
  final _businessNameController = TextEditingController();
  final _addressController = TextEditingController();
  final _repNameController = TextEditingController();
  final _repSsnLast4Controller = TextEditingController();
  bool _kybSubmitting = false;
  String? _kybError;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final user = ref.read(authStateProvider).user;
      if (user?.merchantId != null) {
        ref.read(merchantProvider.notifier).load(user!.merchantId!);
      }
    });
  }

  @override
  void dispose() {
    _einController.dispose();
    _businessNameController.dispose();
    _addressController.dispose();
    _repNameController.dispose();
    _repSsnLast4Controller.dispose();
    super.dispose();
  }

  Future<void> _submitKyb(String merchantId) async {
    final ein = _einController.text.trim();
    final businessName = _businessNameController.text.trim();
    if (ein.isEmpty || businessName.isEmpty) {
      setState(() => _kybError = 'EIN and Business Name are required.');
      return;
    }
    setState(() {
      _kybSubmitting = true;
      _kybError = null;
    });
    final error = await ref.read(merchantProvider.notifier).submitKyb(
          merchantId,
          ein: ein,
          businessName: businessName,
          businessAddress:
              _addressController.text.trim().isNotEmpty ? _addressController.text.trim() : null,
          representativeName:
              _repNameController.text.trim().isNotEmpty ? _repNameController.text.trim() : null,
          representativeSsnLast4: _repSsnLast4Controller.text.trim().isNotEmpty
              ? _repSsnLast4Controller.text.trim()
              : null,
        );
    if (mounted) {
      setState(() {
        _kybSubmitting = false;
        _kybError = error;
      });
    }
  }

  Widget _kybCard(Merchant merchant) {
    switch (merchant.kybStatus) {
      case 'not_required':
        return const SizedBox.shrink();

      case 'approved':
        return Card(
          color: Colors.green.shade50,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                const Icon(Icons.verified, color: Colors.green),
                const SizedBox(width: 12),
                Text(
                  'Business Verified',
                  style: Theme.of(context)
                      .textTheme
                      .titleSmall
                      ?.copyWith(color: Colors.green, fontWeight: FontWeight.bold),
                ),
              ],
            ),
          ),
        );

      case 'pending':
        return Card(
          color: Colors.orange.shade50,
          child: const Padding(
            padding: EdgeInsets.all(16),
            child: Row(
              children: [
                Icon(Icons.hourglass_top, color: Colors.orange),
                SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'KYB Verification Under Review',
                    style: TextStyle(color: Colors.orange),
                  ),
                ),
              ],
            ),
          ),
        );

      case 'rejected':
        return Card(
          color: Colors.red.shade50,
          child: const Padding(
            padding: EdgeInsets.all(16),
            child: Row(
              children: [
                Icon(Icons.error_outline, color: Colors.red),
                SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'KYB Rejected — please contact support.',
                    style: TextStyle(color: Colors.red),
                  ),
                ),
              ],
            ),
          ),
        );

      default: // 'not_submitted'
        if (_einController.text.isEmpty) {
          _einController.text = merchant.ein ?? '';
        }
        if (_businessNameController.text.isEmpty) {
          _businessNameController.text = merchant.name;
        }
        return Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Business Verification (KYB)',
                    style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 4),
                Text(
                  'Submit your business details for verification.',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _einController,
                  decoration: const InputDecoration(
                    labelText: 'EIN *',
                    hintText: '12-3456789',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _businessNameController,
                  decoration: const InputDecoration(
                    labelText: 'Business Name *',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _addressController,
                  decoration: const InputDecoration(
                    labelText: 'Business Address',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _repNameController,
                  decoration: const InputDecoration(
                    labelText: 'Representative Name',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _repSsnLast4Controller,
                  keyboardType: TextInputType.number,
                  maxLength: 4,
                  decoration: const InputDecoration(
                    labelText: 'Representative SSN (last 4)',
                    hintText: '1234',
                    border: OutlineInputBorder(),
                    counterText: '',
                  ),
                ),
                if (_kybError != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      _kybError!,
                      style: TextStyle(
                          color: Theme.of(context).colorScheme.error, fontSize: 12),
                    ),
                  ),
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _kybSubmitting ? null : () => _submitKyb(merchant.id),
                    child: _kybSubmitting
                        ? const SizedBox(
                            height: 18,
                            width: 18,
                            child: CircularProgressIndicator(strokeWidth: 2))
                        : const Text('Submit for Verification'),
                  ),
                ),
              ],
            ),
          ),
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    final merchantState = ref.watch(merchantProvider);

    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Merchant Profile'),
      body: merchantState.when(
        data: (merchant) {
          if (merchant == null) {
            return const Center(child: Text('No merchant data'));
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(merchant.name,
                          style: Theme.of(context).textTheme.titleLarge),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          StatusChip(status: merchant.onboardingStatus),
                          const SizedBox(width: 8),
                          StatusChip(status: merchant.kybStatus),
                        ],
                      ),
                      const SizedBox(height: 16),
                      _infoRow('ID', merchant.id),
                      if (merchant.ein != null) _infoRow('EIN', merchant.ein!),
                      _infoRow('Email', merchant.contactEmail),
                      if (merchant.contactPhone != null)
                        _infoRow('Phone', merchant.contactPhone!),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              _kybCard(merchant),
              if (merchant.kybStatus != 'not_required') const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: () => context.push(RouteNames.bankAccounts),
                icon: const Icon(Icons.account_balance),
                label: const Text('Bank Accounts'),
              ),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }

  Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(label, style: const TextStyle(color: Colors.grey)),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}
