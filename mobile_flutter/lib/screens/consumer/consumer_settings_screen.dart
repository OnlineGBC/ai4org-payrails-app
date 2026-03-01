import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/payrails_app_bar.dart';

class ConsumerSettingsScreen extends ConsumerStatefulWidget {
  const ConsumerSettingsScreen({super.key});

  @override
  ConsumerState<ConsumerSettingsScreen> createState() =>
      _ConsumerSettingsScreenState();
}

class _ConsumerSettingsScreenState
    extends ConsumerState<ConsumerSettingsScreen> {
  late final TextEditingController _phoneController;
  bool _savingPhone = false;
  String? _phoneError;
  String? _phoneSuccess;

  @override
  void initState() {
    super.initState();
    final user = ref.read(authStateProvider).user;
    _phoneController = TextEditingController(text: user?.phone ?? '');
  }

  @override
  void dispose() {
    _phoneController.dispose();
    super.dispose();
  }

  Future<void> _savePhone() async {
    setState(() {
      _savingPhone = true;
      _phoneError = null;
      _phoneSuccess = null;
    });
    try {
      await ref
          .read(authStateProvider.notifier)
          .updatePhone(_phoneController.text.trim());
      if (mounted) setState(() => _phoneSuccess = 'Phone number saved.');
    } catch (e) {
      if (mounted) setState(() => _phoneError = 'Failed to save: $e');
    } finally {
      if (mounted) setState(() => _savingPhone = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(authStateProvider).user;

    return Scaffold(
      appBar: const PayRailsAppBar(title: 'Settings'),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Account info
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Account',
                      style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 12),
                  ListTile(
                    leading: const Icon(Icons.email),
                    title: Text(user?.email ?? 'Not logged in'),
                    subtitle: const Text('Consumer account'),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Phone number
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('SMS Notifications',
                      style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 4),
                  Text(
                    'Enter your mobile number to receive SMS alerts when payments complete.',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _phoneController,
                    keyboardType: TextInputType.phone,
                    decoration: const InputDecoration(
                      labelText: 'Mobile number',
                      hintText: '+15551234567',
                      prefixIcon: Icon(Icons.phone),
                      border: OutlineInputBorder(),
                    ),
                  ),
                  if (_phoneError != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Text(
                        _phoneError!,
                        style: TextStyle(
                            color: Theme.of(context).colorScheme.error,
                            fontSize: 12),
                      ),
                    ),
                  if (_phoneSuccess != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Text(
                        _phoneSuccess!,
                        style: const TextStyle(color: Colors.green, fontSize: 12),
                      ),
                    ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _savingPhone ? null : _savePhone,
                      child: _savingPhone
                          ? const SizedBox(
                              height: 18,
                              width: 18,
                              child:
                                  CircularProgressIndicator(strokeWidth: 2))
                          : const Text('Save Phone Number'),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),

          ElevatedButton.icon(
            onPressed: () => ref.read(authStateProvider.notifier).logout(),
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
