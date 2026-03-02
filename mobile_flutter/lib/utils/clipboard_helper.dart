// Extracted from QR screen files so that clipboard fallback logic can be
// unit-tested independently and shared across screens.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Attempts to copy [text] to the clipboard and shows a SnackBar on success.
/// On failure (e.g. browser blocks clipboard access over HTTP), shows a dialog
/// with a [SelectableText] so the user can copy manually.
Future<void> copyToClipboard(
    BuildContext context, String text, String label) async {
  try {
    await Clipboard.setData(ClipboardData(text: text));
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$label copied')),
      );
    }
  } catch (_) {
    if (context.mounted) {
      showDialog<void>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: Text('Copy $label'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Your browser blocked auto-copy.\nSelect the text below and press Ctrl+C.',
              ),
              const SizedBox(height: 12),
              SelectableText(
                text,
                style: const TextStyle(fontFamily: 'monospace'),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: const Text('Close'),
            ),
          ],
        ),
      );
    }
  }
}
