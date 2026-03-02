// Tests for Issue 4 (Flutter side): User model parses first_name / last_name
// from JSON and stores them correctly.

import 'package:flutter_test/flutter_test.dart';
import 'package:instant_pay_app/models/user.dart';

void main() {
  group('Issue 4 — User model: firstName / lastName fields', () {
    test('fromJson parses both first_name and last_name', () {
      final user = User.fromJson({
        'id': 'u-1',
        'email': 'raja@test.com',
        'role': 'user',
        'first_name': 'Raja',
        'last_name': 'Singh',
      });
      expect(user.firstName, 'Raja');
      expect(user.lastName, 'Singh');
    });

    test('fromJson sets firstName and lastName to null when keys are absent', () {
      final user = User.fromJson({
        'id': 'u-2',
        'email': 'noname@test.com',
        'role': 'user',
      });
      expect(user.firstName, isNull);
      expect(user.lastName, isNull);
    });

    test('fromJson handles explicit null values', () {
      final user = User.fromJson({
        'id': 'u-3',
        'email': 'nullname@test.com',
        'role': 'user',
        'first_name': null,
        'last_name': null,
      });
      expect(user.firstName, isNull);
      expect(user.lastName, isNull);
    });

    test('constructor sets firstName and lastName', () {
      final user = User(
        id: 'u-4',
        email: 'alice@test.com',
        role: 'user',
        firstName: 'Alice',
        lastName: 'Jones',
      );
      expect(user.firstName, 'Alice');
      expect(user.lastName, 'Jones');
    });

    test('firstName only — lastName remains null', () {
      final user = User.fromJson({
        'id': 'u-5',
        'email': 'fn@test.com',
        'role': 'user',
        'first_name': 'Alice',
      });
      expect(user.firstName, 'Alice');
      expect(user.lastName, isNull);
    });

    test('lastName only — firstName remains null', () {
      final user = User.fromJson({
        'id': 'u-6',
        'email': 'ln@test.com',
        'role': 'user',
        'last_name': 'Smith',
      });
      expect(user.firstName, isNull);
      expect(user.lastName, 'Smith');
    });

    test('isConsumer and isMerchant flags unaffected by name fields', () {
      final consumer = User(
          id: 'c', email: 'c@t.com', role: 'user',
          firstName: 'Bob', lastName: 'Smith');
      final merchant = User(
          id: 'm', email: 'm@t.com', role: 'merchant_admin',
          firstName: 'Corp', lastName: 'Owner');

      expect(consumer.isConsumer, isTrue);
      expect(consumer.isMerchant, isFalse);
      expect(merchant.isConsumer, isFalse);
      expect(merchant.isMerchant, isTrue);
    });

    test('other fields still parsed correctly alongside name fields', () {
      final user = User.fromJson({
        'id': 'u-7',
        'email': 'full@test.com',
        'role': 'merchant_admin',
        'merchant_id': 'merch-99',
        'phone': '+15550001234',
        'first_name': 'Full',
        'last_name': 'User',
        'created_at': '2026-01-15T10:00:00.000',
      });
      expect(user.id, 'u-7');
      expect(user.merchantId, 'merch-99');
      expect(user.phone, '+15550001234');
      expect(user.firstName, 'Full');
      expect(user.lastName, 'User');
      expect(user.createdAt, isNotNull);
    });
  });
}
