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

  Future<User> registerMerchant({
    required String email,
    required String password,
    required String businessName,
    required String ein,
    required String contactEmail,
  }) async {
    final response = await _api.post(ApiConfig.registerMerchant, data: {
      'email': email,
      'password': password,
      'business_name': businessName,
      'ein': ein,
      'contact_email': contactEmail,
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

  /// Returns `{message, reset_token}`. `reset_token` is non-null only when the
  /// email is registered (MVP demo — in production this would be emailed).
  Future<Map<String, dynamic>> requestPasswordReset(String email) async {
    final response = await _api.post(
      ApiConfig.passwordResetRequest,
      data: {'email': email},
    );
    return response.data as Map<String, dynamic>;
  }

  Future<void> confirmPasswordReset(String token, String newPassword) async {
    await _api.post(ApiConfig.passwordResetConfirm, data: {
      'token': token,
      'new_password': newPassword,
    });
  }

  Future<User> updateName(String firstName, String lastName) async {
    final response = await _api.patch(ApiConfig.me, data: {
      'first_name': firstName,
      'last_name': lastName,
    });
    return User.fromJson(response.data);
  }
}
