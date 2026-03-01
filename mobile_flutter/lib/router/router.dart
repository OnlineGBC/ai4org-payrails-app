import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/auth_provider.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/register_screen.dart';
import '../screens/dashboard/dashboard_screen.dart';
import '../screens/payments/payment_list_screen.dart';
import '../screens/payments/payment_detail_screen.dart';
import '../screens/payments/send_payment_screen.dart';
import '../screens/merchant/merchant_screen.dart';
import '../screens/bank_accounts/bank_account_list_screen.dart';
import '../screens/bank_accounts/add_bank_account_screen.dart';
import '../screens/bank_accounts/verify_bank_account_screen.dart';
import '../screens/settings/settings_screen.dart';
import '../screens/qr/qr_generate_screen.dart';
import '../screens/qr/qr_scan_screen.dart';
import '../screens/nfc/nfc_pay_screen.dart';
import '../screens/consumer/consumer_dashboard_screen.dart';
import '../screens/consumer/consumer_wallet_screen.dart';
import '../screens/consumer/consumer_pay_confirm_screen.dart';
import '../screens/consumer/consumer_settings_screen.dart';
import 'route_names.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final notifier = ref.read(authChangeNotifierProvider);

  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: notifier,
    redirect: (context, state) {
      final authState = ref.read(authStateProvider);
      final isAuthRoute = state.matchedLocation == RouteNames.login ||
          state.matchedLocation == RouteNames.register;

      // Still checking stored token — don't redirect anywhere yet
      if (authState.status == AuthStatus.unknown) {
        // If already on login/register, stay there; otherwise go to splash
        if (isAuthRoute) return null;
        return '/splash';
      }

      final isAuth = authState.status == AuthStatus.authenticated;

      if (!isAuth && !isAuthRoute) return RouteNames.login;
      if (isAuth && isAuthRoute) {
        // Role-based redirect after login
        final user = authState.user;
        if (user != null && user.role == 'user') {
          return RouteNames.consumerDashboard;
        }
        return RouteNames.dashboard;
      }
      // If authenticated and on splash, redirect to correct dashboard
      if (isAuth && state.matchedLocation == '/splash') {
        final user = authState.user;
        if (user != null && user.role == 'user') {
          return RouteNames.consumerDashboard;
        }
        return RouteNames.dashboard;
      }
      return null;
    },
    errorBuilder: (context, state) => Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Page not found'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => GoRouter.of(context).go(RouteNames.dashboard),
              child: const Text('Go to Dashboard'),
            ),
          ],
        ),
      ),
    ),
    routes: [
      GoRoute(
        path: '/splash',
        builder: (context, state) => const Scaffold(
          body: Center(child: CircularProgressIndicator()),
        ),
      ),
      GoRoute(
        path: RouteNames.login,
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: RouteNames.register,
        builder: (context, state) => const RegisterScreen(),
      ),
      // Merchant shell route
      ShellRoute(
        builder: (context, state, child) => ScaffoldWithNav(child: child),
        routes: [
          GoRoute(
            path: RouteNames.dashboard,
            builder: (context, state) => const DashboardScreen(),
          ),
          GoRoute(
            path: RouteNames.payments,
            builder: (context, state) => const PaymentListScreen(),
          ),
          GoRoute(
            path: RouteNames.settings,
            builder: (context, state) => const SettingsScreen(),
          ),
        ],
      ),
      // Consumer shell route
      ShellRoute(
        builder: (context, state, child) =>
            ConsumerScaffoldWithNav(child: child),
        routes: [
          GoRoute(
            path: RouteNames.consumerDashboard,
            builder: (context, state) => const ConsumerDashboardScreen(),
          ),
          GoRoute(
            path: RouteNames.consumerWallet,
            builder: (context, state) => const ConsumerWalletScreen(),
          ),
          GoRoute(
            path: RouteNames.consumerSettings,
            builder: (context, state) => const ConsumerSettingsScreen(),
          ),
        ],
      ),
      // Standalone routes
      GoRoute(
        path: RouteNames.consumerPayConfirm,
        builder: (context, state) => ConsumerPayConfirmScreen(
          merchantId: state.uri.queryParameters['merchantId'] ?? '',
        ),
      ),
      GoRoute(
        path: RouteNames.sendPayment,
        builder: (context, state) => const SendPaymentScreen(),
      ),
      GoRoute(
        path: '/payments/:id',
        builder: (context, state) => PaymentDetailScreen(
          paymentId: state.pathParameters['id']!,
        ),
      ),
      GoRoute(
        path: RouteNames.merchant,
        builder: (context, state) => const MerchantScreen(),
      ),
      GoRoute(
        path: RouteNames.bankAccounts,
        builder: (context, state) => const BankAccountListScreen(),
      ),
      GoRoute(
        path: RouteNames.addBankAccount,
        builder: (context, state) => const AddBankAccountScreen(),
      ),
      GoRoute(
        path: RouteNames.verifyBankAccount,
        builder: (context, state) => VerifyBankAccountScreen(
          merchantId: state.uri.queryParameters['merchantId']!,
          accountId: state.uri.queryParameters['accountId']!,
          amount1: state.uri.queryParameters['amount1'] ?? '',
          amount2: state.uri.queryParameters['amount2'] ?? '',
        ),
      ),
      GoRoute(
        path: RouteNames.qrGenerate,
        builder: (context, state) => const QrGenerateScreen(),
      ),
      GoRoute(
        path: RouteNames.qrScan,
        builder: (context, state) => const QrScanScreen(),
      ),
      GoRoute(
        path: RouteNames.nfcPay,
        builder: (context, state) => const NfcPayScreen(),
      ),
    ],
  );
});

class ScaffoldWithNav extends StatelessWidget {
  final Widget child;
  const ScaffoldWithNav({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _getIndex(GoRouterState.of(context).matchedLocation),
        onDestinationSelected: (index) {
          switch (index) {
            case 0:
              context.go(RouteNames.dashboard);
              break;
            case 1:
              context.go(RouteNames.payments);
              break;
            case 2:
              context.go(RouteNames.settings);
              break;
          }
        },
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard), label: 'Dashboard'),
          NavigationDestination(icon: Icon(Icons.payment), label: 'Payments'),
          NavigationDestination(icon: Icon(Icons.settings), label: 'Settings'),
        ],
      ),
    );
  }

  int _getIndex(String location) {
    if (location.startsWith(RouteNames.payments)) return 1;
    if (location.startsWith(RouteNames.settings)) return 2;
    return 0;
  }
}

class ConsumerScaffoldWithNav extends StatelessWidget {
  final Widget child;
  const ConsumerScaffoldWithNav({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex:
            _getIndex(GoRouterState.of(context).matchedLocation),
        onDestinationSelected: (index) {
          switch (index) {
            case 0:
              context.go(RouteNames.consumerDashboard);
              break;
            case 1:
              context.go(RouteNames.consumerWallet);
              break;
            case 2:
              context.go(RouteNames.consumerSettings);
              break;
          }
        },
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home), label: 'Home'),
          NavigationDestination(
              icon: Icon(Icons.account_balance_wallet), label: 'Wallet'),
          NavigationDestination(icon: Icon(Icons.settings), label: 'Settings'),
        ],
      ),
    );
  }

  int _getIndex(String location) {
    if (location.startsWith(RouteNames.consumerWallet)) return 1;
    if (location.startsWith(RouteNames.consumerSettings)) return 2;
    return 0;
  }
}
