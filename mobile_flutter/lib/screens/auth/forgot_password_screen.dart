import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/auth_provider.dart';
import '../../router/route_names.dart';

class ForgotPasswordScreen extends ConsumerStatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  ConsumerState<ForgotPasswordScreen> createState() =>
      _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends ConsumerState<ForgotPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  bool _loading = false;
  String? _error;
  String? _resetToken;
  bool _tokenCopied = false;

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _loading = true;
      _error = null;
      _resetToken = null;
      _tokenCopied = false;
    });
    try {
      final authService = ref.read(authServiceProvider);
      final result = await authService.requestPasswordReset(
        _emailController.text.trim(),
      );
      if (mounted) {
        setState(() {
          _loading = false;
          _resetToken = result['reset_token'] as String?;
          if (_resetToken == null) {
            // Unknown email — show generic message without leaking info
            _error =
                'If that email is registered, a reset code has been generated.\n'
                'Check the demo console or try a registered email.';
          }
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = 'Request failed. Please try again.';
        });
      }
    }
  }

  void _copyToken() {
    if (_resetToken == null) return;
    Clipboard.setData(ClipboardData(text: _resetToken!));
    setState(() => _tokenCopied = true);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Forgot Password')),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 400),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      'Reset your password',
                      style: Theme.of(context)
                          .textTheme
                          .headlineSmall
                          ?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Enter your account email. We\'ll generate a reset code.',
                      style: Theme.of(context)
                          .textTheme
                          .bodyMedium
                          ?.copyWith(color: Colors.grey),
                    ),
                    const SizedBox(height: 32),

                    if (_error != null && _resetToken == null)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 16),
                        child: Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.orange.shade50,
                            border: Border.all(color: Colors.orange.shade300),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(_error!,
                              style:
                                  const TextStyle(fontSize: 13)),
                        ),
                      ),

                    TextFormField(
                      controller: _emailController,
                      keyboardType: TextInputType.emailAddress,
                      decoration: const InputDecoration(
                        labelText: 'Email',
                        prefixIcon: Icon(Icons.email_outlined),
                      ),
                      validator: (v) =>
                          v == null || v.isEmpty ? 'Email is required' : null,
                    ),
                    const SizedBox(height: 24),

                    ElevatedButton(
                      onPressed: (_loading || _resetToken != null)
                          ? null
                          : _submit,
                      child: _loading
                          ? const SizedBox(
                              height: 18,
                              width: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Text('Request Reset Code'),
                    ),

                    // Demo token box
                    if (_resetToken != null) ...[
                      const SizedBox(height: 24),
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.blue.shade50,
                          border: Border.all(color: Colors.blue.shade300),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(Icons.info_outline,
                                    color: Colors.blue.shade700, size: 18),
                                const SizedBox(width: 8),
                                Text(
                                  'Demo: Reset Code',
                                  style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      color: Colors.blue.shade700),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            const Text(
                              'In production this code would be emailed. '
                              'Copy it, then tap "Reset Password" below.',
                              style: TextStyle(fontSize: 12),
                            ),
                            const SizedBox(height: 12),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 12, vertical: 8),
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(color: Colors.blue.shade200),
                              ),
                              child: Row(
                                children: [
                                  Expanded(
                                    child: Text(
                                      _resetToken!,
                                      style: const TextStyle(
                                          fontFamily: 'monospace',
                                          fontSize: 11),
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                  IconButton(
                                    icon: Icon(
                                      _tokenCopied
                                          ? Icons.check
                                          : Icons.copy,
                                      color: _tokenCopied
                                          ? Colors.green
                                          : Colors.blue.shade700,
                                      size: 20,
                                    ),
                                    onPressed: _copyToken,
                                    tooltip: 'Copy token',
                                    padding: EdgeInsets.zero,
                                    constraints: const BoxConstraints(),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton.icon(
                        icon: const Icon(Icons.lock_reset),
                        label: const Text('Reset Password'),
                        onPressed: () => context.push(
                          '${RouteNames.resetPassword}'
                          '?token=${Uri.encodeComponent(_resetToken!)}',
                        ),
                      ),
                    ],

                    const SizedBox(height: 16),
                    TextButton(
                      onPressed: () => context.go(RouteNames.login),
                      child: const Text('Back to Sign In'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
