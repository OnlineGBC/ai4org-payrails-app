import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/auth_provider.dart';
import '../../router/route_names.dart';
import '../../widgets/payrails_app_bar.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authStateProvider).user;

    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Settings'),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Account', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 12),
                  ListTile(
                    leading: const Icon(Icons.email),
                    title: Text(user?.email ?? 'Not logged in'),
                    subtitle: Text('Role: ${user?.role ?? 'unknown'}'),
                  ),
                  if (user?.merchantId != null)
                    ListTile(
                      leading: const Icon(Icons.business),
                      title: const Text('Merchant'),
                      subtitle: Text(user!.merchantId!),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => context.push(RouteNames.merchant),
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.account_balance),
                  title: const Text('Bank Accounts'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push(RouteNames.bankAccounts),
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(Icons.qr_code),
                  title: const Text('QR Payment'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push(RouteNames.qrGenerate),
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(Icons.nfc),
                  title: const Text('NFC Payment'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push(RouteNames.nfcPay),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: () {
              ref.read(authStateProvider.notifier).logout();
            },
            icon: const Icon(Icons.logout),
            label: const Text('Logout'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Theme.of(context).colorScheme.error,
              foregroundColor: Colors.white,
            ),
          ),
        ],
      ),
    );
  }
}
