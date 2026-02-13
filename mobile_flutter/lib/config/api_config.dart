class ApiConfig {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );

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
