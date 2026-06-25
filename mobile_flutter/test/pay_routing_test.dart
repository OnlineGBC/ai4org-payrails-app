// Tests for payTargetRoute: a scanned/entered merchant ID must route to the
// correct payment flow based on the payer's role — merchants pay merchant→
// merchant (B2B), consumers pay from their wallet.

import 'package:flutter_test/flutter_test.dart';
import 'package:instant_pay_app/utils/pay_routing.dart';

void main() {
  group('payTargetRoute', () {
    test('consumer (role "user") goes to the consumer pay-confirm flow', () {
      final route = payTargetRoute(role: 'user', merchantId: 'merchant-002');
      expect(route, '/consumer/pay-confirm?merchantId=merchant-002');
    });

    test('merchant_admin goes to the B2B send-payment flow', () {
      final route =
          payTargetRoute(role: 'merchant_admin', merchantId: 'merchant-002');
      expect(route, '/send-payment?receiverMerchantId=merchant-002');
    });

    test('any non-consumer role routes to B2B send-payment', () {
      final route =
          payTargetRoute(role: 'merchant_viewer', merchantId: 'merchant-007');
      expect(route, '/send-payment?receiverMerchantId=merchant-007');
    });

    test('null role defaults to the consumer flow (original behavior)', () {
      final route = payTargetRoute(role: null, merchantId: 'merchant-002');
      expect(route, '/consumer/pay-confirm?merchantId=merchant-002');
    });

    test('merchant ID is URL-encoded', () {
      final route =
          payTargetRoute(role: 'user', merchantId: 'a b&c=d');
      expect(route, '/consumer/pay-confirm?merchantId=a%20b%26c%3Dd');
    });
  });
}
