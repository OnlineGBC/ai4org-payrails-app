import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../models/bank_account.dart';
import '../../providers/auth_provider.dart';
import '../../providers/consumer_provider.dart';
import '../../router/route_names.dart';
import '../../widgets/payrails_app_bar.dart';

class ConsumerWalletScreen extends ConsumerStatefulWidget {
  const ConsumerWalletScreen({super.key});

  @override
  ConsumerState<ConsumerWalletScreen> createState() =>
      _ConsumerWalletScreenState();
}

class _ConsumerWalletScreenState extends ConsumerState<ConsumerWalletScreen> {
  final _amountController = TextEditingController();

  List<BankAccount> _verifiedAccounts = [];
  String? _selectedAccountId;
  bool _loadingAccounts = true;
  bool _funding = false;
  String? _fundError;
  String? _fundSuccess;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      ref.read(walletBalanceProvider.notifier).load();
      await _loadAccounts();
    });
  }

  @override
  void dispose() {
    _amountController.dispose();
    super.dispose();
  }

  Future<void> _loadAccounts() async {
    final user = ref.read(authStateProvider).user;
    if (user?.merchantId == null) {
      setState(() => _loadingAccounts = false);
      return;
    }
    try {
      final accounts =
          await ref.read(consumerServiceProvider).listBankAccounts(user!.merchantId!);
      final verified =
          accounts.where((a) => a.verificationStatus == 'verified').toList();
      setState(() {
        _verifiedAccounts = verified;
        _selectedAccountId =
            verified.isNotEmpty ? verified.first.id : null;
        _loadingAccounts = false;
      });
    } catch (_) {
      setState(() => _loadingAccounts = false);
    }
  }

  Future<void> _addFunds() async {
    final amount = double.tryParse(_amountController.text.trim());
    if (amount == null || amount <= 0) {
      setState(() => _fundError = 'Enter a valid amount.');
      return;
    }
    if (_selectedAccountId == null) {
      setState(() => _fundError = 'Select a bank account.');
      return;
    }
    setState(() {
      _funding = true;
      _fundError = null;
      _fundSuccess = null;
    });
    try {
      final result = await ref
          .read(walletBalanceProvider.notifier)
          .fundWallet(_selectedAccountId!, amount);
      if (mounted) {
        if (result.succeeded) {
          _amountController.clear();
          setState(() => _fundSuccess =
              'Added \$${NumberFormat('#,##0.00').format(amount)} to your wallet.');
        } else {
          setState(() =>
              _fundError = 'Transfer failed: ${result.failureReason ?? 'bank error'}. Please try again.');
        }
      }
    } catch (e) {
      if (mounted) setState(() => _fundError = 'Failed: $e');
    } finally {
      if (mounted) setState(() => _funding = false);
    }
  }

  String _accountLabel(BankAccount a) {
    final name = a.bankName ?? 'Bank';
    final last4 = a.accountNumberLast4 ?? '????';
    return '$name ****$last4';
  }

  @override
  Widget build(BuildContext context) {
    final walletState = ref.watch(walletBalanceProvider);

    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Wallet'),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.read(walletBalanceProvider.notifier).load();
          await _loadAccounts();
        },
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

            // Add Funds card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Add Funds',
                        style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 4),
                    Text(
                      'Transfer money from your linked bank account via ACH.',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    const SizedBox(height: 16),

                    if (_loadingAccounts)
                      const Center(child: CircularProgressIndicator())
                    else if (_verifiedAccounts.isEmpty)
                      _NoVerifiedAccountBanner(
                        onTap: () =>
                            context.push(RouteNames.bankAccounts),
                      )
                    else ...[
                      // Bank account selector
                      DropdownButtonFormField<String>(
                        initialValue: _selectedAccountId,
                        decoration: const InputDecoration(
                          labelText: 'From account',
                          prefixIcon: Icon(Icons.account_balance),
                          border: OutlineInputBorder(),
                        ),
                        items: _verifiedAccounts
                            .map((a) => DropdownMenuItem(
                                  value: a.id,
                                  child: Text(_accountLabel(a)),
                                ))
                            .toList(),
                        onChanged: (v) =>
                            setState(() => _selectedAccountId = v),
                      ),
                      const SizedBox(height: 12),

                      // Amount field
                      TextField(
                        controller: _amountController,
                        keyboardType: const TextInputType.numberWithOptions(
                            decimal: true),
                        decoration: const InputDecoration(
                          labelText: 'Amount',
                          prefixText: '\$ ',
                          border: OutlineInputBorder(),
                        ),
                      ),

                      if (_fundError != null)
                        Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: Text(
                            _fundError!,
                            style: TextStyle(
                                color: Theme.of(context).colorScheme.error,
                                fontSize: 12),
                          ),
                        ),
                      if (_fundSuccess != null)
                        Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: Text(
                            _fundSuccess!,
                            style: const TextStyle(
                                color: Colors.green, fontSize: 12),
                          ),
                        ),

                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: _funding ? null : _addFunds,
                          child: _funding
                              ? const SizedBox(
                                  height: 18,
                                  width: 18,
                                  child: CircularProgressIndicator(
                                      strokeWidth: 2))
                              : const Text('Add Funds'),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _NoVerifiedAccountBanner extends StatelessWidget {
  final VoidCallback onTap;
  const _NoVerifiedAccountBanner({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            Icon(Icons.info_outline,
                color: Theme.of(context).colorScheme.primary),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                'No verified bank account found. Tap to add and verify one in Settings → Bank Accounts.',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
            Icon(Icons.chevron_right,
                color: Theme.of(context).colorScheme.primary),
          ],
        ),
      ),
    );
  }
}
