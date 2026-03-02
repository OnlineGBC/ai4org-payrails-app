// Tests for Issue 2: dangerous keyword detection in transaction descriptions.
// Verifies that nuclear/weapon/drug/etc. keywords trigger a warning regardless
// of merchant type, and that the existing merchant-category mismatch checks
// still work correctly.

import 'package:flutter_test/flutter_test.dart';
import 'package:instant_pay_app/utils/anomaly_detection.dart';

void main() {
  // ---------------------------------------------------------------------------
  // Issue 2 — Dangerous keyword check (universal, before category logic)
  // ---------------------------------------------------------------------------

  group('Dangerous keyword detection — fires for any merchant', () {
    test('nuclear triggers warning at a grocery merchant', () {
      expect(checkAnomaly('WalmartTestCorp', 'nuclear materials'), isNotNull);
    });

    test('nuclear missiles triggers warning at a grocery merchant', () {
      expect(checkAnomaly('WalmartTestCorp', 'nuclear missiles'), isNotNull);
    });

    test('weapon triggers warning at a restaurant merchant', () {
      expect(checkAnomaly('McDonaldsTestCorp', 'buying weapons'), isNotNull);
    });

    test('drug triggers warning at a streaming merchant', () {
      expect(checkAnomaly('Netflix', 'drug purchase'), isNotNull);
    });

    test('cocaine triggers warning at a retail merchant', () {
      expect(checkAnomaly('Nike', 'cocaine for resale'), isNotNull);
    });

    test('bomb triggers warning at an unknown merchant', () {
      expect(checkAnomaly('SomeRandomShop', 'bomb components'), isNotNull);
    });

    test('launder triggers warning at an unknown merchant', () {
      expect(checkAnomaly('LocalCafe', 'launder proceeds'), isNotNull);
    });

    test('warning message contains the ⚠️ symbol', () {
      final w = checkAnomaly('Nike', 'nuclear materials');
      expect(w, contains('⚠️'));
    });

    test('warning message includes the original description', () {
      final w = checkAnomaly('Walmart', 'nuclear missiles for purchase');
      expect(w, contains('nuclear missiles for purchase'));
    });

    test('case-insensitive: NUCLEAR triggers warning', () {
      expect(checkAnomaly('WalmartTestCorp', 'NUCLEAR MATERIALS'), isNotNull);
    });

    test('case-insensitive: Cocaine triggers warning', () {
      expect(checkAnomaly('Target', 'Cocaine purchase'), isNotNull);
    });

    test('dangerous check fires before merchant-category check (unknown merchant)', () {
      // No known merchant category — without the dangerous keyword check the
      // function would return null; with it, it should return a warning.
      expect(checkAnomaly('UnknownStore', 'smuggle goods'), isNotNull);
    });
  });

  // ---------------------------------------------------------------------------
  // Existing merchant-category mismatch checks still work
  // ---------------------------------------------------------------------------

  group('Merchant-category mismatch checks', () {
    test('normal grocery purchase at Walmart returns null', () {
      expect(checkAnomaly('WalmartTestCorp', 'Grocery purchase'), isNull);
    });

    test('financial keyword at grocery store triggers mismatch warning', () {
      final w = checkAnomaly('WalmartTestCorp', 'wire transfer');
      expect(w, isNotNull);
      expect(w, isNot(contains('⚠️'))); // not the dangerous-keyword message
    });

    test('physical goods keyword at Western Union triggers mismatch warning', () {
      expect(
          checkAnomaly('WesternUnionTestCorp', 'buying groceries'), isNotNull);
    });

    test('physical goods keyword at Netflix triggers mismatch warning', () {
      expect(checkAnomaly('Netflix', 'buying shoes'), isNotNull);
    });

    test('normal payment at unknown merchant returns null', () {
      expect(checkAnomaly('LocalCoffeeShop', 'morning coffee'), isNull);
    });

    test('investment keyword at McDonald\'s triggers financial mismatch', () {
      expect(checkAnomaly('McDonaldsTestCorp', 'investment payment'), isNotNull);
    });
  });

  // ---------------------------------------------------------------------------
  // Keyword set completeness
  // ---------------------------------------------------------------------------

  group('kDangerousKeywords completeness', () {
    final required = [
      'nuclear', 'weapon', 'missile', 'explosive', 'bomb', 'grenade',
      'fentanyl', 'cocaine', 'heroin', 'meth', 'drug', 'narcotics',
      'illegal', 'stolen', 'counterfeit', 'smuggle', 'launder',
    ];

    for (final kw in required) {
      test('kDangerousKeywords contains "$kw"', () {
        expect(kDangerousKeywords, contains(kw));
      });
    }
  });
}
