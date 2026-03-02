import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:instant_pay_app/models/transaction.dart';
import 'package:instant_pay_app/widgets/transaction_tile.dart';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

Transaction _make({
  String id = 'txn-1',
  double amount = 100.00,
  String status = 'completed',
  String? rail = 'fednow',
  String? senderMerchantId,
  String? senderUserId,
  String? receiverMerchantId,
  String? receiverUserId,
  String? senderName,
  String? receiverName,
  String description = '',
  DateTime? createdAt,
}) =>
    Transaction(
      id: id,
      amount: amount,
      currency: 'USD',
      status: status,
      idempotencyKey: 'key-$id',
      rail: rail,
      senderMerchantId: senderMerchantId,
      senderUserId: senderUserId,
      receiverMerchantId: receiverMerchantId,
      receiverUserId: receiverUserId,
      senderName: senderName,
      receiverName: receiverName,
      description: description,
      createdAt: createdAt,
    );

Widget _wrap(Widget child) => MaterialApp(home: Scaffold(body: child));

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

void main() {
  group('TransactionTile — amount formatting', () {
    testWidgets('displays amount with no prefix when direction is unknown',
        (tester) async {
      final txn = _make(amount: 100.00);
      await tester.pumpWidget(_wrap(TransactionTile(transaction: txn)));
      expect(find.text(r'$100.00'), findsOneWidget);
    });

    testWidgets('formats large amount with comma separator', (tester) async {
      final txn = _make(amount: 1234.56);
      await tester.pumpWidget(_wrap(TransactionTile(transaction: txn)));
      expect(find.text(r'$1,234.56'), findsOneWidget);
    });

    testWidgets('formats amount with two decimal places', (tester) async {
      final txn = _make(amount: 50.0);
      await tester.pumpWidget(_wrap(TransactionTile(transaction: txn)));
      expect(find.text(r'$50.00'), findsOneWidget);
    });
  });

  group('TransactionTile — sent direction (merchant)', () {
    testWidgets('shows minus prefix and Sent label when currentMerchantId matches sender',
        (tester) async {
      final txn = _make(
        amount: 50.00,
        senderMerchantId: 'merch-a',
        receiverMerchantId: 'merch-b',
      );
      await tester.pumpWidget(_wrap(TransactionTile(
        transaction: txn,
        currentMerchantId: 'merch-a',
      )));
      expect(find.text(r'- $50.00'), findsOneWidget);
      expect(find.text('Sent'), findsOneWidget);
    });
  });

  group('TransactionTile — received direction (merchant)', () {
    testWidgets('shows plus prefix and Received label when currentMerchantId matches receiver',
        (tester) async {
      final txn = _make(
        amount: 75.00,
        senderMerchantId: 'merch-a',
        receiverMerchantId: 'merch-b',
      );
      await tester.pumpWidget(_wrap(TransactionTile(
        transaction: txn,
        currentMerchantId: 'merch-b',
      )));
      expect(find.text(r'+ $75.00'), findsOneWidget);
      expect(find.text('Received'), findsOneWidget);
    });
  });

  group('TransactionTile — sent direction (consumer user)', () {
    testWidgets('shows Sent label when currentUserId matches senderUserId',
        (tester) async {
      final txn = _make(
        amount: 30.00,
        senderUserId: 'user-abc',
        receiverMerchantId: 'merch-x',
      );
      await tester.pumpWidget(_wrap(TransactionTile(
        transaction: txn,
        currentUserId: 'user-abc',
      )));
      expect(find.text('Sent'), findsOneWidget);
      expect(find.text(r'- $30.00'), findsOneWidget);
    });
  });

  group('TransactionTile — neutral direction', () {
    testWidgets('shows no Sent or Received label when no currentId is given',
        (tester) async {
      final txn = _make(
        amount: 25.00,
        senderMerchantId: 'merch-a',
        receiverMerchantId: 'merch-b',
      );
      await tester.pumpWidget(_wrap(TransactionTile(transaction: txn)));
      expect(find.text('Sent'), findsNothing);
      expect(find.text('Received'), findsNothing);
    });
  });

  group('TransactionTile — From → To display', () {
    testWidgets('shows sender → receiver line when both names present',
        (tester) async {
      final txn = _make(senderName: 'Acme Corp', receiverName: 'Globex Inc');
      await tester.pumpWidget(_wrap(TransactionTile(transaction: txn)));
      expect(find.text('Acme Corp → Globex Inc'), findsOneWidget);
    });

    testWidgets('hides From → To line when both names are null',
        (tester) async {
      final txn = _make(); // no senderName, no receiverName
      await tester.pumpWidget(_wrap(TransactionTile(transaction: txn)));
      expect(find.textContaining('→'), findsNothing);
    });

    testWidgets('shows partial line with ? when only sender name is known',
        (tester) async {
      final txn = _make(senderName: 'Alice', receiverName: null);
      await tester.pumpWidget(_wrap(TransactionTile(transaction: txn)));
      expect(find.text('Alice → ?'), findsOneWidget);
    });

    testWidgets('shows partial line with ? when only receiver name is known',
        (tester) async {
      final txn = _make(senderName: null, receiverName: 'Bob Corp');
      await tester.pumpWidget(_wrap(TransactionTile(transaction: txn)));
      expect(find.text('? → Bob Corp'), findsOneWidget);
    });

    testWidgets('consumer email shown as sender name in consumer-to-merchant flow',
        (tester) async {
      final txn = _make(
        senderName: 'consumer1@test.com',
        receiverName: 'Acme Corp',
        senderUserId: 'user-consumer-001',
      );
      await tester.pumpWidget(_wrap(TransactionTile(transaction: txn)));
      expect(find.text('consumer1@test.com → Acme Corp'), findsOneWidget);
    });
  });

  group('TransactionTile — description display', () {
    testWidgets('shows description text when non-empty', (tester) async {
      final txn = _make(description: 'Grocery payment for weekly shop');
      await tester.pumpWidget(_wrap(TransactionTile(transaction: txn)));
      expect(find.text('Grocery payment for weekly shop'), findsOneWidget);
    });

    testWidgets('hides description row when description is empty',
        (tester) async {
      final txn = _make(description: '');
      await tester.pumpWidget(_wrap(TransactionTile(transaction: txn)));
      // Tile renders without error; no description text in the widget tree
      expect(find.byType(TransactionTile), findsOneWidget);
      expect(find.text(''), findsNothing);
    });
  });

  group('TransactionTile — status chip', () {
    testWidgets('shows COMPLETED chip for completed status', (tester) async {
      final txn = _make(status: 'completed');
      await tester.pumpWidget(_wrap(TransactionTile(transaction: txn)));
      expect(find.text('COMPLETED'), findsOneWidget);
    });

    testWidgets('shows FAILED chip for failed status', (tester) async {
      final txn = _make(status: 'failed');
      await tester.pumpWidget(_wrap(TransactionTile(transaction: txn)));
      expect(find.text('FAILED'), findsOneWidget);
    });

    testWidgets('shows PROCESSING chip for processing status', (tester) async {
      final txn = _make(status: 'processing');
      await tester.pumpWidget(_wrap(TransactionTile(transaction: txn)));
      expect(find.text('PROCESSING'), findsOneWidget);
    });
  });

  group('TransactionTile — rail badge', () {
    testWidgets('shows FEDNOW badge when rail is fednow', (tester) async {
      final txn = _make(rail: 'fednow');
      await tester.pumpWidget(_wrap(TransactionTile(transaction: txn)));
      expect(find.text('FEDNOW'), findsOneWidget);
    });

    testWidgets('shows ACH badge when rail is ach', (tester) async {
      final txn = _make(rail: 'ach');
      await tester.pumpWidget(_wrap(TransactionTile(transaction: txn)));
      expect(find.text('ACH'), findsOneWidget);
    });

    testWidgets('shows no badge when rail is null', (tester) async {
      final txn = _make(rail: null);
      await tester.pumpWidget(_wrap(TransactionTile(transaction: txn)));
      // No rail badge text at all
      expect(find.text('FEDNOW'), findsNothing);
      expect(find.text('ACH'), findsNothing);
    });
  });

  group('TransactionTile — tap callback', () {
    testWidgets('triggers onTap when tile is tapped', (tester) async {
      bool tapped = false;
      final txn = _make();
      await tester.pumpWidget(_wrap(TransactionTile(
        transaction: txn,
        onTap: () => tapped = true,
      )));
      await tester.tap(find.byType(ListTile));
      expect(tapped, isTrue);
    });

    testWidgets('no error when onTap is null', (tester) async {
      final txn = _make();
      await tester.pumpWidget(_wrap(TransactionTile(transaction: txn)));
      await tester.tap(find.byType(ListTile));
      // Just verify no exception is thrown
      expect(find.byType(TransactionTile), findsOneWidget);
    });
  });
}
