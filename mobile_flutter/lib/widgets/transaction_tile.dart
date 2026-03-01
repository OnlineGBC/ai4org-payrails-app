import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/transaction.dart';
import 'status_chip.dart';
import 'rail_badge.dart';

class TransactionTile extends StatelessWidget {
  final Transaction transaction;
  final VoidCallback? onTap;
  final String? currentMerchantId;
  final String? currentUserId;

  const TransactionTile({
    super.key,
    required this.transaction,
    this.onTap,
    this.currentMerchantId,
    this.currentUserId,
  });

  bool get _isSent {
    if (currentMerchantId != null) {
      return transaction.senderMerchantId == currentMerchantId;
    }
    if (currentUserId != null) {
      return transaction.senderUserId == currentUserId;
    }
    return false;
  }

  bool get _isReceived {
    if (currentMerchantId != null) {
      return transaction.receiverMerchantId == currentMerchantId &&
          transaction.senderMerchantId != currentMerchantId;
    }
    return false;
  }

  @override
  Widget build(BuildContext context) {
    final sent = _isSent;
    final received = _isReceived;

    final IconData icon;
    final Color iconBg;
    final Color iconColor;
    final String prefix;
    final Color amountColor;
    final String label;

    if (sent) {
      icon = Icons.arrow_upward;
      iconBg = Colors.red.shade50;
      iconColor = Colors.red.shade700;
      prefix = '- ';
      amountColor = Colors.red.shade700;
      label = 'Sent';
    } else if (received) {
      icon = Icons.arrow_downward;
      iconBg = Colors.green.shade50;
      iconColor = Colors.green.shade700;
      prefix = '+ ';
      amountColor = Colors.green.shade700;
      label = 'Received';
    } else {
      icon = Icons.swap_horiz;
      iconBg = Theme.of(context).colorScheme.primaryContainer;
      iconColor = Theme.of(context).colorScheme.primary;
      prefix = '';
      amountColor = Theme.of(context).textTheme.bodyLarge?.color ?? Colors.black;
      label = '';
    }

    final formattedAmount =
        NumberFormat('#,##0.00').format(transaction.amount);

    return ListTile(
      onTap: onTap,
      leading: CircleAvatar(
        backgroundColor: iconBg,
        child: Icon(icon, color: iconColor),
      ),
      title: Text(
        '$prefix\$$formattedAmount',
        style: TextStyle(fontWeight: FontWeight.w600, color: amountColor),
      ),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              if (label.isNotEmpty) ...[
                Text(label,
                    style: TextStyle(
                        fontSize: 12,
                        color: sent
                            ? Colors.red.shade400
                            : Colors.green.shade400)),
                const SizedBox(width: 8),
              ],
              RailBadge(rail: transaction.rail),
              const SizedBox(width: 8),
              if (transaction.createdAt != null)
                Text(
                  _formatDate(transaction.createdAt!),
                  style: Theme.of(context).textTheme.bodySmall,
                ),
            ],
          ),
          if (transaction.description?.isNotEmpty == true)
            Text(
              transaction.description!,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    fontStyle: FontStyle.italic,
                    color: Colors.grey.shade600,
                  ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
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
