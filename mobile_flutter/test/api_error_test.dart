// Tests for friendlyApiError: ensures backend errors are turned into short,
// user-facing messages instead of raw "DioException [bad response]..." dumps.

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:instant_pay_app/utils/api_error.dart';

DioException _dioWith({int? statusCode, dynamic data, DioExceptionType? type}) {
  final req = RequestOptions(path: '/consumer/pay');
  return DioException(
    requestOptions: req,
    type: type ?? DioExceptionType.badResponse,
    response: statusCode == null
        ? null
        : Response(requestOptions: req, statusCode: statusCode, data: data),
  );
}

void main() {
  group('friendlyApiError', () {
    test('prefers the backend detail message when present', () {
      final e = _dioWith(
        statusCode: 403,
        data: {'detail': 'Only consumers can make wallet payments'},
      );
      expect(friendlyApiError(e), 'Only consumers can make wallet payments');
    });

    test('falls back to a friendly 403 message when no detail', () {
      final e = _dioWith(statusCode: 403, data: {});
      expect(friendlyApiError(e),
          "You don't have permission to do that with this account.");
    });

    test('401 always returns the session-expired message', () {
      final e = _dioWith(statusCode: 401, data: {'detail': 'Invalid token'});
      expect(friendlyApiError(e), 'Your session has expired. Please sign in again.');
    });

    test('no response (network/timeout) returns a connection message', () {
      final e = _dioWith(type: DioExceptionType.connectionTimeout);
      expect(friendlyApiError(e),
          "Can't reach the server. Check your connection and try again.");
    });

    test('5xx returns a generic server-error message', () {
      final e = _dioWith(statusCode: 500, data: 'Internal Server Error');
      expect(friendlyApiError(e),
          'Something went wrong on our end. Please try again shortly.');
    });

    test('non-Dio errors never leak the raw exception string', () {
      final msg = friendlyApiError(Exception('boom'));
      expect(msg, 'Something went wrong. Please try again.');
      expect(msg.contains('Exception'), isFalse);
    });
  });
}
