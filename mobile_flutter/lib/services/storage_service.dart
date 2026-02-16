import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

class StorageService {
  static const _accessTokenKey = 'access_token';
  static const _refreshTokenKey = 'refresh_token';

  final FlutterSecureStorage _storage = const FlutterSecureStorage(
    webOptions: WebOptions(
      dbName: 'PayRailsSecureStorage',
      publicKey: 'PayRailsPublicKey',
    ),
  );

  // Fallback for web on HTTP (crypto.subtle unavailable)
  // Uses SharedPreferences (localStorage on web) so tokens survive refresh.
  bool? _useFallback;

  Future<bool> _shouldUseFallback() async {
    if (!kIsWeb) return false;
    if (_useFallback != null) return _useFallback!;
    try {
      await _storage.write(key: '_probe', value: 'ok');
      await _storage.delete(key: '_probe');
      _useFallback = false;
    } catch (_) {
      _useFallback = true;
    }
    return _useFallback!;
  }

  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    if (await _shouldUseFallback()) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_accessTokenKey, accessToken);
      await prefs.setString(_refreshTokenKey, refreshToken);
    } else {
      await _storage.write(key: _accessTokenKey, value: accessToken);
      await _storage.write(key: _refreshTokenKey, value: refreshToken);
    }
  }

  Future<String?> getAccessToken() async {
    if (await _shouldUseFallback()) {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getString(_accessTokenKey);
    }
    return await _storage.read(key: _accessTokenKey);
  }

  Future<String?> getRefreshToken() async {
    if (await _shouldUseFallback()) {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getString(_refreshTokenKey);
    }
    return await _storage.read(key: _refreshTokenKey);
  }

  Future<void> clearTokens() async {
    if (await _shouldUseFallback()) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_accessTokenKey);
      await prefs.remove(_refreshTokenKey);
    } else {
      await _storage.delete(key: _accessTokenKey);
      await _storage.delete(key: _refreshTokenKey);
    }
  }
}
