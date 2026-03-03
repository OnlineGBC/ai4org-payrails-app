import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../models/bank_account.dart';
import '../../providers/auth_provider.dart';
import '../../providers/bank_account_provider.dart';
import '../../router/route_names.dart';
import '../../widgets/payrails_app_bar.dart';
import '../../widgets/status_chip.dart';

class BankAccountListScreen extends ConsumerStatefulWidget {
  const BankAccountListScreen({super.key});

  @override
  ConsumerState<BankAccountListScreen> createState() => _BankAccountListScreenState();
}

class _BankAccountListScreenState extends ConsumerState<BankAccountListScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _reload());
  }

  void _reload() {
    final user = ref.read(authStateProvider).user;
    if (user?.merchantId != null) {
      ref.read(bankAccountListProvider.notifier).load(user!.merchantId!);
    }
  }

  Future<void> _pushVerify(BankAccount acct) async {
    final user = ref.read(authStateProvider).user;
    await context.push(
      '${RouteNames.verifyBankAccount}'
      '?merchantId=${user!.merchantId!}'
      '&accountId=${acct.id}'
      '&amount1=${acct.microDepositAmount1 ?? ""}'
      '&amount2=${acct.microDepositAmount2 ?? ""}',
    );
    _reload();
  }

  Future<void> _addAccount() async {
    final result = await context.push<BankAccount>(RouteNames.addBankAccount);
    _reload();
    // If a new unverified account was returned, navigate straight to verify
    if (result != null && result.verificationStatus != 'verified' && mounted) {
      await _pushVerify(result);
    }
  }

  String _subtitle(BankAccount acct) {
    switch (acct.verificationStatus) {
      case 'micro_deposit_sent':
        return 'Tap to verify — enter the two micro-deposit amounts';
      case 'pending':
        return 'Tap to verify this account';
      case 'verified':
        return 'Routing: ${acct.routingNumber} · ****${acct.accountNumberLast4 ?? ""}';
      default:
        return 'Routing: ${acct.routingNumber} · ****${acct.accountNumberLast4 ?? ""}';
    }
  }

  @override
  Widget build(BuildContext context) {
    final accountsState = ref.watch(bankAccountListProvider);

    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Bank Accounts'),
      floatingActionButton: FloatingActionButton(
        onPressed: _addAccount,
        tooltip: 'Add Bank Account',
        child: const Icon(Icons.add),
      ),
      body: accountsState.when(
        data: (accounts) {
          if (accounts.isEmpty) {
            return const Center(child: Text('No bank accounts linked'));
          }
          return ListView.builder(
            padding: const EdgeInsets.all(8),
            itemCount: accounts.length,
            itemBuilder: (context, index) {
              final acct = accounts[index];
              final needsVerification = acct.verificationStatus != 'verified';
              return Card(
                child: ListTile(
                  leading: CircleAvatar(
                    backgroundColor: needsVerification
                        ? Colors.orange.shade50
                        : Colors.green.shade50,
                    child: Icon(
                      Icons.account_balance,
                      color: needsVerification ? Colors.orange : Colors.green,
                    ),
                  ),
                  title: Text(acct.bankName ?? 'Bank Account'),
                  subtitle: Text(
                    _subtitle(acct),
                    style: TextStyle(
                      color: needsVerification ? Colors.orange.shade700 : null,
                      fontSize: 12,
                    ),
                  ),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      StatusChip(status: acct.verificationStatus),
                      if (needsVerification)
                        const Icon(Icons.chevron_right, color: Colors.grey),
                    ],
                  ),
                  onTap: () {
                    if (acct.verificationStatus == 'verified') {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Account already verified')),
                      );
                    } else {
                      _pushVerify(acct);
                    }
                  },
                ),
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
