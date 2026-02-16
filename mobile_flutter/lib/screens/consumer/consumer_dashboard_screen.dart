import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/auth_provider.dart';
import '../../providers/consumer_provider.dart';
import '../../router/route_names.dart';
import '../../widgets/payrails_app_bar.dart';

class ConsumerDashboardScreen extends ConsumerStatefulWidget {
  const ConsumerDashboardScreen({super.key});

  @override
  ConsumerState<ConsumerDashboardScreen> createState() =>
      _ConsumerDashboardScreenState();
}

class _ConsumerDashboardScreenState
    extends ConsumerState<ConsumerDashboardScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadData());
  }

  void _loadData() {
    ref.read(walletBalanceProvider.notifier).load();
  }

  @override
  Widget build(BuildContext context) {
    final walletState = ref.watch(walletBalanceProvider);
    final user = ref.watch(authStateProvider).user;

    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Home'),
      body: RefreshIndicator(
        onRefresh: () async => _loadData(),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Wallet balance card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Wallet Balance',
                        style: Theme.of(context).textTheme.bodySmall),
                    const SizedBox(height: 8),
                    walletState.when(
                      data: (b) => Text(
                        b != null
                            ? '\$${b.balance.toStringAsFixed(2)}'
                            : '\$0.00',
                        style: Theme.of(context)
                            .textTheme
                            .headlineLarge
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      loading: () => const CircularProgressIndicator(),
                      error: (e, _) => Text('Error: $e'),
                    ),
                    const SizedBox(height: 8),
                    if (user != null)
                      Text(user.email,
                          style: Theme.of(context).textTheme.bodySmall),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Quick actions
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () => context.push(RouteNames.qrScan),
                icon: const Icon(Icons.qr_code_scanner),
                label: const Text('Scan QR to Pay'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
