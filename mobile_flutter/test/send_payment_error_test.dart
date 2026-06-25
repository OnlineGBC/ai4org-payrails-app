// Verifies the Send Payment (B2B) screen renders a friendly message when a
// payment fails, instead of dumping the raw "DioException [bad response]..."
// string. This is the merchant→merchant flow merchants are routed to after a
// QR scan, so a failure here must read cleanly.

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:instant_pay_app/models/transaction.dart';
import 'package:instant_pay_app/models/user.dart';
import 'package:instant_pay_app/providers/auth_provider.dart';
import 'package:instant_pay_app/providers/payment_provider.dart';
import 'package:instant_pay_app/screens/payments/send_payment_screen.dart';
import 'package:instant_pay_app/services/auth_service.dart';
import 'package:instant_pay_app/services/payment_service.dart';

/// PaymentService stub whose sendPayment always fails with a 403 + detail,
/// mirroring the backend's "Only merchant admins can initiate B2B payments".
class _ThrowingPaymentService implements PaymentService {
  @override
  Future<Transaction> sendPayment({
    required String senderMerchantId,
    required String receiverMerchantId,
    required double amount,
    required String idempotencyKey,
    String? preferredRail,
    String? description,
  }) async {
    throw DioException(
      requestOptions: RequestOptions(path: '/payments'),
      response: Response(
        requestOptions: RequestOptions(path: '/payments'),
        statusCode: 403,
        data: {'detail': 'Only merchant admins can initiate B2B payments'},
      ),
    );
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _FakeAuthService implements AuthService {
  @override
  dynamic noSuchMethod(Invocation invocation) => Future<dynamic>.value(null);
}

/// Auth notifier pre-seeded with an authenticated merchant so the form's
/// merchant-association check passes and we reach the network call.
class _FakeAuthNotifier extends AuthNotifier {
  _FakeAuthNotifier() : super(_FakeAuthService()) {
    state = AuthState(
      status: AuthStatus.authenticated,
      user: User(
        id: 'u-001',
        email: 'merchant@test.com',
        role: 'merchant_admin',
        merchantId: 'merchant-001',
      ),
    );
  }

  @override
  Future<void> checkAuth() async {}
}

void main() {
  testWidgets('Send Payment shows a friendly error, not a raw DioException',
      (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          paymentServiceProvider.overrideWithValue(_ThrowingPaymentService()),
          authStateProvider.overrideWith((ref) => _FakeAuthNotifier()),
        ],
        // NoSplash avoids the InkSparkle fragment-shader load, which fails to
        // decode in the headless test runner (a Flutter SDK quirk, not our code).
        child: MaterialApp(
          theme: ThemeData(splashFactory: NoSplash.splashFactory),
          home: const SendPaymentScreen(),
        ),
      ),
    );

    // Fill the form: receiver, amount, description (in source order).
    final fields = find.byType(TextFormField);
    await tester.enterText(fields.at(0), 'merchant-002');
    await tester.enterText(fields.at(1), '100');
    await tester.enterText(fields.at(2), 'Payment');

    final sendButton = find.widgetWithText(ElevatedButton, 'Send Payment');
    await tester.ensureVisible(sendButton);
    await tester.tap(sendButton);
    await tester.pumpAndSettle();

    // Friendly backend detail is shown; the raw exception class is not.
    expect(find.text('Only merchant admins can initiate B2B payments'),
        findsOneWidget);
    expect(find.textContaining('DioException'), findsNothing);
  });

  testWidgets('demo disclaimer uses a dark, readable color (contrast guard)',
      (tester) async {
    // The disclaimer sits on a pale amber box; without an explicit color the
    // text inherits the dark theme's light color and becomes unreadable.
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authStateProvider.overrideWith((ref) => _FakeAuthNotifier()),
        ],
        child: const MaterialApp(home: SendPaymentScreen()),
      ),
    );

    final disclaimer =
        tester.widget<Text>(find.textContaining('MVP Demo Environment'));
    expect(disclaimer.style?.color, const Color(0xFF4E342E));
  });
}
