import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/auth_provider.dart';
import '../../providers/balance_provider.dart';
import '../../providers/payment_provider.dart';
import '../../router/route_names.dart';
import '../../widgets/payrails_app_bar.dart';
import '../../widgets/transaction_tile.dart';

class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({super.key});

  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadData());
  }

  void _loadData() {
    final user = ref.read(authStateProvider).user;
    if (user?.merchantId != null) {
      ref.read(balanceProvider.notifier).load(user!.merchantId!);
      ref.read(transactionListProvider.notifier).load(user.merchantId!);
    }
  }

  @override
  Widget build(BuildContext context) {
    final balanceState = ref.watch(balanceProvider);
    final txnState = ref.watch(transactionListProvider);
    final user = ref.watch(authStateProvider).user;

    return Scaffold(
      appBar: PayRailsAppBar(
        title: 'Dashboard',
        actions: [
          IconButton(
            icon: const Icon(Icons.qr_code),
            tooltip: 'QR Payment',
            onPressed: () => context.push(RouteNames.qrGenerate),
          ),
          IconButton(
            icon: const Icon(Icons.nfc),
            tooltip: 'NFC Payment',
            onPressed: () => context.push(RouteNames.nfcPay),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async => _loadData(),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Balance card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Available Balance',
                        style: Theme.of(context).textTheme.bodySmall),
                    const SizedBox(height: 8),
                    balanceState.when(
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
                    if (user?.merchantId != null)
                      Text('Merchant: ${user!.merchantId}',
                          style: Theme.of(context).textTheme.bodySmall),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Quick actions
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () => context.push(RouteNames.sendPayment),
                    icon: const Icon(Icons.send),
                    label: const Text('Send'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => context.push(RouteNames.qrScan),
                    icon: const Icon(Icons.qr_code_scanner),
                    label: const Text('Scan QR'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Recent transactions
            Text('Recent Transactions',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            txnState.when(
              data: (transactions) {
                if (transactions.isEmpty) {
                  return const Padding(
                    padding: EdgeInsets.all(32),
                    child: Center(child: Text('No transactions yet')),
                  );
                }
                return Column(
                  children: transactions.take(5).map((txn) {
                    return TransactionTile(
                      transaction: txn,
                      onTap: () => context.push('/payments/${txn.id}'),
                    );
                  }).toList(),
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Text('Error loading transactions: $e'),
            ),
          ],
        ),
      ),
    );
  }
}
