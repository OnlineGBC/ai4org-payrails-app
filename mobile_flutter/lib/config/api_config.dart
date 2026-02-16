import 'package:flutter/foundation.dart' show kIsWeb, TargetPlatform, defaultTargetPlatform;

class ApiConfig {
  static String get baseUrl {
    // Compile-time override takes priority
    const envUrl = String.fromEnvironment('API_BASE_URL');
    if (envUrl.isNotEmpty) return envUrl;

    // Web: empty string → relative URLs (nginx proxies to backend)
    // For local dev without Docker, set API_BASE_URL=http://localhost:8000
    if (kIsWeb) return '';
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://192.168.1.88:8080';
    }
    return 'http://192.168.1.88:8080';
  }

  // Auth
  static const String register = '/auth/register';
  static const String login = '/auth/login';
  static const String refresh = '/auth/refresh';
  static const String me = '/auth/me';

  // Payments
  static const String payments = '/payments';
  static const String balance = '/payments/balance';
  static const String payouts = '/payments/payouts';

  // Merchants
  static const String merchants = '/merchants';

  // Webhooks
  static const String bankWebhook = '/webhooks/bank';
}
