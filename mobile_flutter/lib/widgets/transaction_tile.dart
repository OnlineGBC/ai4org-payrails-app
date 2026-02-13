import 'package:flutter/material.dart';
import '../models/transaction.dart';
import 'status_chip.dart';
import 'rail_badge.dart';

class TransactionTile extends StatelessWidget {
  final Transaction transaction;
  final VoidCallback? onTap;

  const TransactionTile({super.key, required this.transaction, this.onTap});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      onTap: onTap,
      leading: CircleAvatar(
        backgroundColor: Theme.of(context).colorScheme.primaryContainer,
        child: Icon(
          Icons.swap_horiz,
          color: Theme.of(context).colorScheme.primary,
        ),
      ),
      title: Text(
        '\$${transaction.amount.toStringAsFixed(2)}',
        style: const TextStyle(fontWeight: FontWeight.w600),
      ),
      subtitle: Row(
        children: [
          RailBadge(rail: transaction.rail),
          const SizedBox(width: 8),
          if (transaction.createdAt != null)
            Text(
              _formatDate(transaction.createdAt!),
              style: Theme.of(context).textTheme.bodySmall,
            ),
        ],
      ),
      trailing: StatusChip(status: transaction.status),
    );
  }

  String _formatDate(DateTime dt) {
    return '${dt.month}/${dt.day} ${dt.hour}:${dt.minute.toString().padLeft(2, '0')}';
  }
}
