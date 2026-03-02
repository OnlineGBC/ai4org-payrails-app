// Tests for Issue 1: clipboard copy fallback on HTTP contexts.
// Verifies that:
//   - Successful clipboard write shows a SnackBar
//   - Failed clipboard write (browser blocks it) shows a fallback dialog
//     with SelectableText so the user can copy manually

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:instant_pay_app/utils/clipboard_helper.dart';

// Helper: renders a minimal app that exposes a BuildContext via a Builder,
// calls copyToClipboard on it, then pumps so widgets render.
Future<void> _invoke(
  WidgetTester tester,
  String text,
  String label,
) async {
  late BuildContext ctx;
  await tester.pumpWidget(MaterialApp(
    home: Builder(builder: (c) {
      ctx = c;
      return const Scaffold(body: SizedBox());
    }),
  ));
  await copyToClipboard(ctx, text, label);
  await tester.pumpAndSettle();
}

void main() {
  group('Issue 1 — copyToClipboard: success path', () {
    setUp(() {
      // Allow clipboard writes to succeed
      tester_binding_setClipboard(succeed: true);
    });

    testWidgets('shows SnackBar with "<label> copied" on success',
        (tester) async {
      _setupClipboard(tester, succeed: true);
      await _invoke(tester, 'merchant-001', 'Merchant ID');
      expect(find.text('Merchant ID copied'), findsOneWidget);
    });

    testWidgets('no dialog appears on success', (tester) async {
      _setupClipboard(tester, succeed: true);
      await _invoke(tester, 'user-abc', 'User ID');
      expect(find.byType(AlertDialog), findsNothing);
    });
  });

  group('Issue 1 — copyToClipboard: fallback path (clipboard throws)', () {
    testWidgets('shows AlertDialog with the label in the title', (tester) async {
      _setupClipboard(tester, succeed: false);
      await _invoke(tester, 'merchant-001', 'Merchant ID');
      expect(find.text('Copy Merchant ID'), findsOneWidget);
    });

    testWidgets('dialog contains the "browser blocked" instruction text',
        (tester) async {
      _setupClipboard(tester, succeed: false);
      await _invoke(tester, 'merchant-001', 'Merchant ID');
      expect(
        find.text(
            'Your browser blocked auto-copy.\nSelect the text below and press Ctrl+C.'),
        findsOneWidget,
      );
    });

    testWidgets('dialog contains the ID value as SelectableText', (tester) async {
      _setupClipboard(tester, succeed: false);
      await _invoke(tester, 'my-special-id-123', 'User ID');
      expect(find.text('my-special-id-123'), findsOneWidget);
      expect(find.byType(SelectableText), findsOneWidget);
    });

    testWidgets('no SnackBar when clipboard fails', (tester) async {
      _setupClipboard(tester, succeed: false);
      await _invoke(tester, 'merchant-001', 'Merchant ID');
      expect(find.byType(SnackBar), findsNothing);
    });

    testWidgets('dialog has a Close button that dismisses it', (tester) async {
      _setupClipboard(tester, succeed: false);
      await _invoke(tester, 'some-id', 'Some Label');

      expect(find.text('Copy Some Label'), findsOneWidget);
      await tester.tap(find.text('Close'));
      await tester.pumpAndSettle();
      expect(find.text('Copy Some Label'), findsNothing);
    });

    testWidgets('works with User ID label', (tester) async {
      _setupClipboard(tester, succeed: false);
      await _invoke(tester, 'user-xyz', 'User ID');
      expect(find.text('Copy User ID'), findsOneWidget);
      expect(find.text('user-xyz'), findsOneWidget);
    });
  });
}

// ---------------------------------------------------------------------------
// Test helpers
// ---------------------------------------------------------------------------

/// Mocks the platform clipboard channel to succeed or throw.
void _setupClipboard(WidgetTester tester, {required bool succeed}) {
  tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(
    SystemChannels.platform,
    (MethodCall call) async {
      if (call.method == 'Clipboard.setData') {
        if (!succeed) {
          throw PlatformException(
            code: 'UNAVAILABLE',
            message: 'Clipboard not available (simulated HTTP block)',
          );
        }
        return null;
      }
      return null;
    },
  );
}

// Dummy top-level so the setUp group compiles — actual setup is per-test.
void tester_binding_setClipboard({required bool succeed}) {}
