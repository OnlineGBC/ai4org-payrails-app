import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/auth_provider.dart';
import '../../router/route_names.dart';
import '../../widgets/error_banner.dart';
import '../../widgets/loading_overlay.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();
  final _businessNameController = TextEditingController();
  final _einController = TextEditingController();
  final _contactEmailController = TextEditingController();

  String _selectedRole = 'consumer';

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _confirmController.dispose();
    _businessNameController.dispose();
    _einController.dispose();
    _contactEmailController.dispose();
    super.dispose();
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedRole == 'merchant') {
      ref.read(authStateProvider.notifier).registerMerchant(
            email: _emailController.text.trim(),
            password: _passwordController.text,
            businessName: _businessNameController.text.trim(),
            ein: _einController.text.trim(),
            contactEmail: _contactEmailController.text.trim(),
          );
    } else {
      ref.read(authStateProvider.notifier).register(
            _emailController.text.trim(),
            _passwordController.text,
          );
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authStateProvider);
    final isMerchant = _selectedRole == 'merchant';

    return Scaffold(
      body: LoadingOverlay(
        isLoading: authState.isLoading,
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 400),
                child: Form(
                  key: _formKey,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'Create Account',
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                      const SizedBox(height: 24),
                      // Role selector
                      SegmentedButton<String>(
                        segments: const [
                          ButtonSegment(
                            value: 'consumer',
                            label: Text('Consumer'),
                            icon: Icon(Icons.person),
                          ),
                          ButtonSegment(
                            value: 'merchant',
                            label: Text('Merchant'),
                            icon: Icon(Icons.business),
                          ),
                        ],
                        selected: {_selectedRole},
                        onSelectionChanged: (selection) {
                          setState(() => _selectedRole = selection.first);
                        },
                      ),
                      const SizedBox(height: 24),
                      ErrorBanner(message: authState.error),
                      TextFormField(
                        controller: _emailController,
                        decoration: const InputDecoration(
                          labelText: 'Email',
                          prefixIcon: Icon(Icons.email_outlined),
                        ),
                        keyboardType: TextInputType.emailAddress,
                        validator: (v) =>
                            v == null || v.isEmpty ? 'Email is required' : null,
                      ),
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _passwordController,
                        decoration: const InputDecoration(
                          labelText: 'Password',
                          prefixIcon: Icon(Icons.lock_outlined),
                        ),
                        obscureText: true,
                        validator: (v) {
                          if (v == null || v.isEmpty) return 'Password is required';
                          if (v.length < 6) return 'At least 6 characters';
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _confirmController,
                        decoration: const InputDecoration(
                          labelText: 'Confirm Password',
                          prefixIcon: Icon(Icons.lock_outlined),
                        ),
                        obscureText: true,
                        validator: (v) {
                          if (v != _passwordController.text) {
                            return 'Passwords do not match';
                          }
                          return null;
                        },
                      ),
                      // Merchant-only fields
                      if (isMerchant) ...[
                        const SizedBox(height: 16),
                        TextFormField(
                          controller: _businessNameController,
                          decoration: const InputDecoration(
                            labelText: 'Business Name',
                            prefixIcon: Icon(Icons.store_outlined),
                          ),
                          validator: (v) => isMerchant && (v == null || v.isEmpty)
                              ? 'Business name is required'
                              : null,
                        ),
                        const SizedBox(height: 16),
                        TextFormField(
                          controller: _einController,
                          decoration: const InputDecoration(
                            labelText: 'EIN',
                            hintText: '12-3456789',
                            prefixIcon: Icon(Icons.numbers_outlined),
                          ),
                          validator: (v) => isMerchant && (v == null || v.isEmpty)
                              ? 'EIN is required'
                              : null,
                        ),
                        const SizedBox(height: 16),
                        TextFormField(
                          controller: _contactEmailController,
                          decoration: const InputDecoration(
                            labelText: 'Contact Email',
                            prefixIcon: Icon(Icons.alternate_email),
                          ),
                          keyboardType: TextInputType.emailAddress,
                          validator: (v) => isMerchant && (v == null || v.isEmpty)
                              ? 'Contact email is required'
                              : null,
                        ),
                      ],
                      const SizedBox(height: 24),
                      ElevatedButton(
                        onPressed: authState.isLoading ? null : _submit,
                        child: const Text('Register'),
                      ),
                      const SizedBox(height: 16),
                      TextButton(
                        onPressed: () => context.go(RouteNames.login),
                        child: const Text('Already have an account? Sign In'),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
