import '../router/route_names.dart';

/// Decides which payment screen a scanned/entered merchant ID should open,
/// based on the current user's role.
///
/// PayRails has two distinct payment models, so the same scanned merchant ID
/// routes differently depending on who is paying:
///
/// - **Consumers** (`role == 'user'`) pay from their prepaid wallet via the
///   consumer pay-confirm flow (`POST /consumer/pay`).
/// - **Merchants** (any non-consumer role) pay merchant→merchant bank-to-bank
///   via the B2B Send Payment flow (`POST /payments`), with the receiver
///   pre-filled.
///
/// A null role (user not loaded) defaults to the consumer flow, preserving the
/// original behavior.
String payTargetRoute({required String? role, required String merchantId}) {
  final encoded = Uri.encodeComponent(merchantId);
  final isConsumer = role == null || role == 'user';
  if (isConsumer) {
    return '${RouteNames.consumerPayConfirm}?merchantId=$encoded';
  }
  return '${RouteNames.sendPayment}?receiverMerchantId=$encoded';
}
