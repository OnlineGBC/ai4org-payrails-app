import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
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

  @override
  Widget build(BuildContext context) {
    final accountsState = ref.watch(bankAccountListProvider);

    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Bank Accounts'),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push(RouteNames.addBankAccount).then((_) => _reload()),
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
              return Card(
                child: ListTile(
                  leading: const CircleAvatar(child: Icon(Icons.account_balance)),
                  title: Text(acct.bankName ?? 'Bank Account'),
                  subtitle: Text(
                    'Routing: ${acct.routingNumber} | ****${acct.accountNumberLast4 ?? ""}',
                  ),
                  trailing: StatusChip(status: acct.verificationStatus),
                  onTap: () {
                    if (acct.verificationStatus == 'verified') {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Already verified')),
                      );
                    } else {
                      final user = ref.read(authStateProvider).user;
                      context.push(
                        '${RouteNames.verifyBankAccount}?merchantId=${user!.merchantId!}&accountId=${acct.id}',
                      ).then((_) => _reload());
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
