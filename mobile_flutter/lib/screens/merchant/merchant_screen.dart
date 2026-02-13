import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
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
                      if (merchant.ein != null)
                        _infoRow('EIN', merchant.ein!),
                      _infoRow('Email', merchant.contactEmail),
                      if (merchant.contactPhone != null)
                        _infoRow('Phone', merchant.contactPhone!),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
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
