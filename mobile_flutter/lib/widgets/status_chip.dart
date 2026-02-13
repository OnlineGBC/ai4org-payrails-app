import 'package:flutter/material.dart';

class StatusChip extends StatelessWidget {
  final String status;

  const StatusChip({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    return Chip(
      label: Text(
        status.toUpperCase(),
        style: TextStyle(color: _textColor, fontSize: 11, fontWeight: FontWeight.w600),
      ),
      backgroundColor: _bgColor,
      padding: EdgeInsets.zero,
      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
    );
  }

  Color get _bgColor {
    switch (status.toLowerCase()) {
      case 'completed':
      case 'verified':
      case 'active':
      case 'approved':
        return const Color(0xFFE6F4EA);
      case 'failed':
      case 'rejected':
      case 'suspended':
        return const Color(0xFFFCE8E6);
      case 'pending':
      case 'processing':
      case 'micro_deposit_sent':
        return const Color(0xFFFEF7E0);
      case 'cancelled':
        return const Color(0xFFF1F3F4);
      default:
        return const Color(0xFFF1F3F4);
    }
  }

  Color get _textColor {
    switch (status.toLowerCase()) {
      case 'completed':
      case 'verified':
      case 'active':
      case 'approved':
        return const Color(0xFF137333);
      case 'failed':
      case 'rejected':
      case 'suspended':
        return const Color(0xFFC5221F);
      case 'pending':
      case 'processing':
      case 'micro_deposit_sent':
        return const Color(0xFFB06000);
      case 'cancelled':
        return const Color(0xFF5F6368);
      default:
        return const Color(0xFF5F6368);
    }
  }
}
