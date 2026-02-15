import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/user.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart';

final authServiceProvider = Provider<AuthService>((ref) {
  final api = ref.read(apiClientProvider);
  final storage = ref.read(storageServiceProvider);
  return AuthService(api, storage);
});

final authStateProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final authService = ref.read(authServiceProvider);
  return AuthNotifier(authService);
});

enum AuthStatus { unknown, authenticated, unauthenticated }

class AuthState {
  final AuthStatus status;
  final User? user;
  final String? error;
  final bool isLoading;

  const AuthState({
    this.status = AuthStatus.unknown,
    this.user,
    this.error,
    this.isLoading = false,
  });

  AuthState copyWith({
    AuthStatus? status,
    User? user,
    String? error,
    bool? isLoading,
  }) {
    return AuthState(
      status: status ?? this.status,
      user: user ?? this.user,
      error: error,
      isLoading: isLoading ?? this.isLoading,
    );
  }
}

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthService _authService;

  AuthNotifier(this._authService) : super(const AuthState()) {
    checkAuth();
  }

  Future<void> checkAuth() async {
    try {
      final loggedIn = await _authService.isLoggedIn();
      if (loggedIn) {
        final user = await _authService.getMe();
        state = AuthState(status: AuthStatus.authenticated, user: user);
      } else {
        state = const AuthState(status: AuthStatus.unauthenticated);
      }
    } catch (_) {
      state = const AuthState(status: AuthStatus.unauthenticated);
    }
  }

  Future<void> login(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      await _authService.login(email, password);
      final user = await _authService.getMe();
      state = AuthState(status: AuthStatus.authenticated, user: user);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Login failed. Check your credentials.',
      );
    }
  }

  Future<void> register(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      await _authService.register(email, password);
      await login(email, password);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Registration failed. Email may already be in use.',
      );
    }
  }

  Future<void> logout() async {
    await _authService.logout();
    state = const AuthState(status: AuthStatus.unauthenticated);
  }
}

/// Bridges Riverpod [authStateProvider] to a [ChangeNotifier] so GoRouter
/// can use it as a [refreshListenable] without recreating the router.
class AuthChangeNotifier extends ChangeNotifier {
  AuthChangeNotifier(Ref ref) {
    ref.listen<AuthState>(authStateProvider, (_, __) {
      notifyListeners();
    });
  }
}

final authChangeNotifierProvider = Provider<AuthChangeNotifier>((ref) {
  return AuthChangeNotifier(ref);
});
