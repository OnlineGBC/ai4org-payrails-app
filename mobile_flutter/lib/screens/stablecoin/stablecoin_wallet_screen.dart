import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../models/stablecoin.dart';
import '../../providers/stablecoin_provider.dart';
import '../../router/route_names.dart';
import '../../widgets/payrails_app_bar.dart';

final _fmt = NumberFormat('#,##0.######');

class StablecoinWalletScreen extends ConsumerStatefulWidget {
  const StablecoinWalletScreen({super.key});

  @override
  ConsumerState<StablecoinWalletScreen> createState() =>
      _StablecoinWalletScreenState();
}

class _StablecoinWalletScreenState
    extends ConsumerState<StablecoinWalletScreen> {
  Future<List<StablecoinTx>>? _txFuture;
  bool _submittingKyc = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _refresh());
  }

  void _refresh() {
    ref.read(stablecoinWalletProvider.notifier).load();
    setState(() {
      _txFuture = ref.read(stablecoinServiceProvider).listTransactions();
    });
  }

  Future<void> _verifyIdentity() async {
    setState(() => _submittingKyc = true);
    try {
      await ref.read(stablecoinWalletProvider.notifier).submitKyc();
      _refresh();
    } finally {
      if (mounted) setState(() => _submittingKyc = false);
    }
  }

  Future<void> _openAction(String route) async {
    await context.push(route);
    _refresh();
  }

  @override
  Widget build(BuildContext context) {
    final walletState = ref.watch(stablecoinWalletProvider);

    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Stablecoins'),
      body: RefreshIndicator(
        onRefresh: () async => _refresh(),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const _DisclosureBanner(),
            const SizedBox(height: 16),
            walletState.when(
              loading: () => const Padding(
                padding: EdgeInsets.all(32),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (e, _) => Text('Error: $e'),
              data: (s) => s.kycApproved
                  ? _buildApproved(context, s)
                  : _buildKycGate(context),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildKycGate(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Verify your identity',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 4),
            Text(
              'Identity verification (KYC) is required before you can hold or '
              'move stablecoins. This is handled by our regulated partner.',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _submittingKyc ? null : _verifyIdentity,
                child: _submittingKyc
                    ? const SizedBox(
                        height: 18,
                        width: 18,
                        child: CircularProgressIndicator(strokeWidth: 2))
                    : const Text('Verify identity (KYC)'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildApproved(BuildContext context, StablecoinWalletState s) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Balances',
                    style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 12),
                for (final b in s.balances)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 6),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(b.assetCode,
                            style: Theme.of(context).textTheme.titleSmall),
                        Text(_fmt.format(b.balance),
                            style: Theme.of(context)
                                .textTheme
                                .titleMedium
                                ?.copyWith(fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: [
            _ActionButton(
              icon: Icons.add,
              label: 'Buy',
              onTap: () => _openAction(RouteNames.stablecoinBuy),
            ),
            _ActionButton(
              icon: Icons.sell,
              label: 'Sell',
              onTap: () => _openAction(RouteNames.stablecoinSell),
            ),
            _ActionButton(
              icon: Icons.north_east,
              label: 'Send',
              onTap: () => _openAction(RouteNames.stablecoinSend),
            ),
            _ActionButton(
              icon: Icons.qr_code,
              label: 'Receive',
              onTap: () => _openAction(RouteNames.stablecoinReceive),
            ),
          ],
        ),
        const SizedBox(height: 24),
        Text('Recent Activity',
            style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        FutureBuilder<List<StablecoinTx>>(
          future: _txFuture,
          builder: (context, snap) {
            if (snap.connectionState == ConnectionState.waiting) {
              return const Padding(
                padding: EdgeInsets.all(16),
                child: Center(child: CircularProgressIndicator()),
              );
            }
            final txns = snap.data ?? [];
            if (txns.isEmpty) {
              return const Padding(
                padding: EdgeInsets.all(16),
                child: Text('No stablecoin activity yet.'),
              );
            }
            return Column(
              children: [for (final t in txns) _TxTile(tx: t)],
            );
          },
        ),
      ],
    );
  }
}

class _DisclosureBanner extends StatelessWidget {
  const _DisclosureBanner();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.amber.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.amber),
      ),
      child: Row(
        children: [
          const Icon(Icons.info_outline, color: Colors.amber),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              'Stablecoins are held with a regulated partner and are NOT '
              'FDIC-insured. Demo environment — do not send real assets.',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
        ],
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _ActionButton(
      {required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 88,
      child: Column(
        children: [
          Material(
            color: Theme.of(context).colorScheme.primaryContainer,
            borderRadius: BorderRadius.circular(12),
            child: InkWell(
              borderRadius: BorderRadius.circular(12),
              onTap: onTap,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Icon(icon,
                    color: Theme.of(context).colorScheme.onPrimaryContainer),
              ),
            ),
          ),
          const SizedBox(height: 6),
          Text(label, style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
    );
  }
}

class _TxTile extends StatelessWidget {
  final StablecoinTx tx;
  const _TxTile({required this.tx});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      dense: true,
      leading: CircleAvatar(
        radius: 16,
        child: Icon(_iconFor(tx.direction), size: 16),
      ),
      title: Text('${_labelFor(tx.direction)} ${tx.assetCode}'),
      subtitle: Text(tx.status),
      trailing: Text('${_fmt.format(tx.amount)} ${tx.assetCode}'),
    );
  }

  IconData _iconFor(String direction) {
    switch (direction) {
      case 'onramp':
      case 'deposit':
        return Icons.south_west;
      case 'send':
      case 'offramp':
        return Icons.north_east;
      default:
        return Icons.swap_horiz;
    }
  }

  String _labelFor(String direction) {
    switch (direction) {
      case 'onramp':
        return 'Bought';
      case 'offramp':
        return 'Sold';
      case 'deposit':
        return 'Received';
      case 'send':
        return 'Sent';
      default:
        return direction;
    }
  }
}
