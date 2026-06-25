import 'package:dio/dio.dart';

/// Converts an exception into a short, user-facing message.
///
/// Prefers the backend's own `detail` text when it provides one; otherwise
/// maps the HTTP status code to a friendly fallback. Never returns a raw
/// exception dump (e.g. "DioException [bad response]...").
String friendlyApiError(Object error) {
  if (error is DioException) {
    final status = error.response?.statusCode;

    // No response at all → network failure / timeout.
    if (status == null) {
      return "Can't reach the server. Check your connection and try again.";
    }

    // Use the backend's own message when one is present.
    final data = error.response?.data;
    String? detail;
    if (data is Map && data['detail'] is String) {
      detail = data['detail'] as String;
    }

    switch (status) {
      case 400:
        return detail ??
            "That request couldn't be completed. Please check the details and try again.";
      case 401:
        return 'Your session has expired. Please sign in again.';
      case 403:
        return detail ?? "You don't have permission to do that with this account.";
      case 404:
        return detail ?? "We couldn't find what you were looking for.";
      case 409:
        return detail ?? 'This looks like a duplicate request.';
      default:
        if (status >= 500) {
          return 'Something went wrong on our end. Please try again shortly.';
        }
        return detail ?? 'Something went wrong. Please try again.';
    }
  }
  return 'Something went wrong. Please try again.';
}
