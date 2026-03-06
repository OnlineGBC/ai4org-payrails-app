import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../models/bank_config.dart';
import '../../providers/auth_provider.dart';
import '../../providers/merchant_provider.dart';
import '../../widgets/payrails_app_bar.dart';

class AddBankAccountScreen extends ConsumerStatefulWidget {
  const AddBankAccountScreen({super.key});

  @override
  ConsumerState<AddBankAccountScreen> createState() => _AddBankAccountScreenState();
}

class _AddBankAccountScreenState extends ConsumerState<AddBankAccountScreen> {
  final _formKey = GlobalKey<FormState>();
  final _routingController = TextEditingController();
  final _accountController = TextEditingController();
  final _bankNameController = TextEditingController();
  bool _isLoading = false;
  String? _error;

  @override
  void dispose() {
    _routingController.dispose();
    _accountController.dispose();
    _bankNameController.dispose();
    super.dispose();
  }

  /// Extract a human-readable message from any exception.
  String _friendlyError(Object e) {
    if (e is DioException) {
      final data = e.response?.data;
      if (data is Map && data['detail'] != null) {
        return data['detail'].toString();
      }
      final code = e.response?.statusCode;
      if (code != null) return 'Server error ($code). Please try again.';
    }
    return e.toString();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    final user = ref.read(authStateProvider).user;
    if (user?.merchantId == null) return;

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final service = ref.read(merchantServiceProvider);
      final account = await service.addBankAccount(
        user!.merchantId!,
        routingNumber: _routingController.text.trim(),
        accountNumber: _accountController.text.trim(),
        bankName: _bankNameController.text.trim().isEmpty
            ? null
            : _bankNameController.text.trim(),
      );

      if (mounted) {
        context.pop(account);
      }
    } catch (e) {
      setState(() => _error = _friendlyError(e));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _showBankSearch() async {
    final service = ref.read(merchantServiceProvider);
    List<BankConfig> banks = [];
    String? loadError;

    try {
      banks = await service.getSupportedBanks();
    } catch (e) {
      loadError = _friendlyError(e);
    }

    if (!mounted) return;

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => _BankSearchSheet(
        banks: banks,
        loadError: loadError,
        onSelected: (bank) {
          Navigator.pop(ctx);
          setState(() => _bankNameController.text = bank.bankName);
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Link Bank Account'),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (_error != null)
                Container(
                  padding: const EdgeInsets.all(12),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: Colors.red.shade50,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(_error!, style: TextStyle(color: Colors.red.shade700)),
                ),
              TextFormField(
                controller: _bankNameController,
                decoration: InputDecoration(
                  labelText: 'Bank Name (optional)',
                  prefixIcon: const Icon(Icons.business),
                  suffixIcon: TextButton(
                    onPressed: _showBankSearch,
                    child: const Text('Browse'),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _routingController,
                decoration: const InputDecoration(
                  labelText: 'Routing Number',
                  prefixIcon: Icon(Icons.numbers),
                ),
                keyboardType: TextInputType.number,
                maxLength: 9,
                validator: (v) {
                  if (v == null || v.length != 9) return 'Must be 9 digits';
                  return null;
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _accountController,
                decoration: const InputDecoration(
                  labelText: 'Account Number',
                  prefixIcon: Icon(Icons.lock_outlined),
                ),
                keyboardType: TextInputType.number,
                validator: (v) {
                  if (v == null || v.length < 4) return 'At least 4 digits';
                  return null;
                },
              ),
              const SizedBox(height: 32),
              ElevatedButton(
                onPressed: _isLoading ? null : _submit,
                child: _isLoading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Link Account'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Bank search bottom sheet
// ---------------------------------------------------------------------------

class _BankSearchSheet extends StatefulWidget {
  final List<BankConfig> banks;
  final String? loadError;
  final ValueChanged<BankConfig> onSelected;

  const _BankSearchSheet({
    required this.banks,
    required this.loadError,
    required this.onSelected,
  });

  @override
  State<_BankSearchSheet> createState() => _BankSearchSheetState();
}

class _BankSearchSheetState extends State<_BankSearchSheet> {
  final _searchController = TextEditingController();
  late List<BankConfig> _filtered;

  @override
  void initState() {
    super.initState();
    _filtered = widget.banks;
    _searchController.addListener(_onSearch);
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _onSearch() {
    final q = _searchController.text.toLowerCase();
    setState(() {
      _filtered = widget.banks
          .where((b) => b.bankName.toLowerCase().contains(q))
          .toList();
    });
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.65,
      minChildSize: 0.4,
      maxChildSize: 0.9,
      builder: (_, scrollController) => Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Drag handle
            Center(
              child: Container(
                width: 40,
                height: 4,
                margin: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(
                  color: Colors.grey.shade300,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            Text('Supported Banks',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            TextField(
              controller: _searchController,
              autofocus: true,
              decoration: InputDecoration(
                hintText: 'Search banks…',
                prefixIcon: const Icon(Icons.search),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
                isDense: true,
              ),
            ),
            const SizedBox(height: 8),
            if (widget.loadError != null)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 16),
                child: Text(
                  'Could not load banks: ${widget.loadError}',
                  style: TextStyle(color: Colors.red.shade700),
                ),
              )
            else if (_filtered.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 24),
                child: Center(child: Text('No banks match your search.')),
              )
            else
              Expanded(
                child: ListView.separated(
                  controller: scrollController,
                  itemCount: _filtered.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (_, i) {
                    final bank = _filtered[i];
                    return ListTile(
                      leading: const Icon(Icons.account_balance),
                      title: Text(bank.bankName),
                      subtitle: Wrap(
                        spacing: 4,
                        children: bank.supportedRails
                            .where((r) => r != 'card')
                            .map((r) => Chip(
                                  label: Text(r.toUpperCase(),
                                      style: const TextStyle(fontSize: 10)),
                                  padding: EdgeInsets.zero,
                                  visualDensity: VisualDensity.compact,
                                ))
                            .toList(),
                      ),
                      onTap: () => widget.onSelected(bank),
                    );
                  },
                ),
              ),
          ],
        ),
      ),
    );
  }
}
