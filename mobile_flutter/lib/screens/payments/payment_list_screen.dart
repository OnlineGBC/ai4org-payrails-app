import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/auth_provider.dart';
import '../../providers/payment_provider.dart';
import '../../router/route_names.dart';
import '../../widgets/payrails_app_bar.dart';
import '../../widgets/transaction_tile.dart';

class PaymentListScreen extends ConsumerStatefulWidget {
  const PaymentListScreen({super.key});

  @override
  ConsumerState<PaymentListScreen> createState() => _PaymentListScreenState();
}

class _PaymentListScreenState extends ConsumerState<PaymentListScreen> {
  final _scrollController = ScrollController();
  String? _statusFilter;
  String? _railFilter;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadData());
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _loadData() {
    final user = ref.read(authStateProvider).user;
    if (user?.merchantId != null) {
      ref.read(transactionListProvider.notifier).load(
            user!.merchantId!,
            status: _statusFilter,
            rail: _railFilter,
          );
    }
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      ref.read(transactionListProvider.notifier).loadMore();
    }
  }

  bool get _hasActiveFilters => _statusFilter != null || _railFilter != null;

  Future<void> _showFilterSheet() async {
    // Local copies so the sheet can mutate without affecting the screen until Apply
    String? tempStatus = _statusFilter;
    String? tempRail = _railFilter;

    await showModalBottomSheet<void>(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setSheetState) {
          return Padding(
            padding: const EdgeInsets.fromLTRB(24, 12, 24, 32),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Drag handle
                Center(
                  child: Container(
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(
                      color: Colors.grey.shade300,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Text('Filter Transactions',
                    style: Theme.of(ctx).textTheme.titleMedium),
                const SizedBox(height: 20),

                // Status filter
                Text('Status', style: Theme.of(ctx).textTheme.labelLarge),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 4,
                  children: [
                    for (final s in <String?>[
                      null,
                      'pending',
                      'processing',
                      'completed',
                      'failed',
                      'cancelled',
                    ])
                      ChoiceChip(
                        label: Text(s == null
                            ? 'All'
                            : '${s[0].toUpperCase()}${s.substring(1)}'),
                        selected: tempStatus == s,
                        onSelected: (_) =>
                            setSheetState(() => tempStatus = s),
                      ),
                  ],
                ),
                const SizedBox(height: 20),

                // Rail filter
                Text('Rail', style: Theme.of(ctx).textTheme.labelLarge),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 4,
                  children: [
                    for (final r in <String?>[null, 'fednow', 'rtp', 'ach'])
                      ChoiceChip(
                        label: Text(r == null ? 'All' : r.toUpperCase()),
                        selected: tempRail == r,
                        onSelected: (_) =>
                            setSheetState(() => tempRail = r),
                      ),
                  ],
                ),
                const SizedBox(height: 24),

                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () => setSheetState(() {
                          tempStatus = null;
                          tempRail = null;
                        }),
                        child: const Text('Clear'),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: ElevatedButton(
                        onPressed: () {
                          Navigator.pop(ctx);
                          setState(() {
                            _statusFilter = tempStatus;
                            _railFilter = tempRail;
                          });
                          _loadData();
                        },
                        child: const Text('Apply'),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final txnState = ref.watch(transactionListProvider);

    return Scaffold(
      appBar: PayRailsAppBar(
        title: 'Transactions',
        actions: [
          Stack(
            children: [
              IconButton(
                icon: const Icon(Icons.filter_list),
                tooltip: 'Filter',
                onPressed: _showFilterSheet,
              ),
              if (_hasActiveFilters)
                Positioned(
                  right: 8,
                  top: 8,
                  child: Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.primary,
                      shape: BoxShape.circle,
                    ),
                  ),
                ),
            ],
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
            onPressed: _loadData,
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push(RouteNames.sendPayment),
        tooltip: 'Send Payment',
        child: const Icon(Icons.add),
      ),
      body: txnState.when(
        data: (transactions) {
          if (transactions.isEmpty) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.receipt_long, size: 48, color: Colors.grey),
                  const SizedBox(height: 12),
                  Text(
                    _hasActiveFilters
                        ? 'No transactions match the current filters'
                        : 'No transactions yet',
                    style: const TextStyle(color: Colors.grey),
                  ),
                  if (_hasActiveFilters) ...[
                    const SizedBox(height: 12),
                    TextButton(
                      onPressed: () {
                        setState(() {
                          _statusFilter = null;
                          _railFilter = null;
                        });
                        _loadData();
                      },
                      child: const Text('Clear filters'),
                    ),
                  ],
                ],
              ),
            );
          }
          return ListView.separated(
            controller: _scrollController,
            padding: const EdgeInsets.symmetric(vertical: 8),
            itemCount: transactions.length,
            separatorBuilder: (_, __) => const Divider(height: 1),
            itemBuilder: (context, index) {
              final txn = transactions[index];
              final user = ref.read(authStateProvider).user;
              return TransactionTile(
                transaction: txn,
                currentMerchantId: user?.merchantId,
                onTap: () => context.push('/payments/${txn.id}'),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }
}
