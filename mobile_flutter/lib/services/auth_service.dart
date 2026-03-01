import '../config/api_config.dart';
import '../models/user.dart';
import '../models/token_pair.dart';
import 'api_client.dart';
import 'storage_service.dart';

class AuthService {
  final ApiClient _api;
  final StorageService _storage;

  AuthService(this._api, this._storage);

  Future<TokenPair> login(String email, String password) async {
    final response = await _api.post(ApiConfig.login, data: {
      'email': email,
      'password': password,
    });
    final tokens = TokenPair.fromJson(response.data);
    await _storage.saveTokens(
      accessToken: tokens.accessToken,
      refreshToken: tokens.refreshToken,
    );
    return tokens;
  }

  Future<User> register(String email, String password) async {
    final response = await _api.post(ApiConfig.register, data: {
      'email': email,
      'password': password,
    });
    return User.fromJson(response.data);
  }

  Future<User> getMe() async {
    final response = await _api.get(ApiConfig.me);
    return User.fromJson(response.data);
  }

  Future<void> logout() async {
    await _storage.clearTokens();
  }

  Future<bool> isLoggedIn() async {
    final token = await _storage.getAccessToken();
    return token != null;
  }

  Future<User> updatePhone(String phone) async {
    final response = await _api.patch(ApiConfig.me, data: {'phone': phone});
    return User.fromJson(response.data);
  }

  Future<User> updateEmail(String email) async {
    final response = await _api.patch(ApiConfig.me, data: {'email': email});
    return User.fromJson(response.data);
  }
}
