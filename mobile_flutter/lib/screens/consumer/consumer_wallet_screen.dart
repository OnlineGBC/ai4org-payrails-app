import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../providers/consumer_provider.dart';
import '../../widgets/payrails_app_bar.dart';

class ConsumerWalletScreen extends ConsumerStatefulWidget {
  const ConsumerWalletScreen({super.key});

  @override
  ConsumerState<ConsumerWalletScreen> createState() =>
      _ConsumerWalletScreenState();
}

class _ConsumerWalletScreenState extends ConsumerState<ConsumerWalletScreen> {
  final _amountController = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(walletBalanceProvider.notifier).load();
    });
  }

  @override
  void dispose() {
    _amountController.dispose();
    super.dispose();
  }

  void _topUp() async {
    final amount = double.tryParse(_amountController.text);
    if (amount == null || amount <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Enter a valid amount')),
      );
      return;
    }
    await ref.read(walletBalanceProvider.notifier).topUp(amount);
    _amountController.clear();
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Topped up \$${NumberFormat('#,##0.00').format(amount)}')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final walletState = ref.watch(walletBalanceProvider);

    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Wallet'),
      body: RefreshIndicator(
        onRefresh: () async => ref.read(walletBalanceProvider.notifier).load(),
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
                    Text('Current Balance',
                        style: Theme.of(context).textTheme.bodySmall),
                    const SizedBox(height: 8),
                    walletState.when(
                      data: (b) => Text(
                        b != null
                            ? '\$${NumberFormat('#,##0.00').format(b.balance)}'
                            : '\$0.00',
                        style: Theme.of(context)
                            .textTheme
                            .headlineLarge
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      loading: () => const CircularProgressIndicator(),
                      error: (e, _) => Text('Error: $e'),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Top up section
            Text('Top Up Wallet',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            TextField(
              controller: _amountController,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'Amount',
                prefixText: '\$ ',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _topUp,
                child: const Text('Top Up'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
