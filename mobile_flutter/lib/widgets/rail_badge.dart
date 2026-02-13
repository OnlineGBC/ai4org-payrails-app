import 'package:flutter/material.dart';

class RailBadge extends StatelessWidget {
  final String? rail;

  const RailBadge({super.key, this.rail});

  @override
  Widget build(BuildContext context) {
    if (rail == null) return const SizedBox.shrink();

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: _bgColor,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        rail!.toUpperCase(),
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.bold,
          color: _textColor,
        ),
      ),
    );
  }

  Color get _bgColor {
    switch (rail?.toLowerCase()) {
      case 'fednow':
        return const Color(0xFFE8EAF6);
      case 'rtp':
        return const Color(0xFFE0F2F1);
      case 'ach':
        return const Color(0xFFFFF3E0);
      case 'card':
        return const Color(0xFFFCE4EC);
      default:
        return const Color(0xFFF1F3F4);
    }
  }

  Color get _textColor {
    switch (rail?.toLowerCase()) {
      case 'fednow':
        return const Color(0xFF283593);
      case 'rtp':
        return const Color(0xFF00695C);
      case 'ach':
        return const Color(0xFFE65100);
      case 'card':
        return const Color(0xFFC62828);
      default:
        return const Color(0xFF5F6368);
    }
  }
}
