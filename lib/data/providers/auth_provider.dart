import 'package:flutter/foundation.dart';
import 'package:smart_turf/core/exceptions/auth_exception.dart';
import 'package:smart_turf/data/models/user_model.dart';
import 'package:smart_turf/data/repositories/auth_repository.dart';

enum AuthStatus {
  initial,
  authenticating,
  authenticated,
  unauthenticated,
  error,
}

class AuthProvider with ChangeNotifier {
  final AuthRepository _authRepository;

  AuthStatus _status = AuthStatus.initial;
  UserModel? _currentUser;
  String? _errorMessage;
  bool _isEmailVerified = false;

  AuthProvider({
    required AuthRepository authRepository,
  }) : _authRepository = authRepository {
    // Initialiser l'état d'authentification au démarrage
    _initAuth();

    // Écouter les changements d'état d'authentification
    _authRepository.authStateChanges.listen((isAuthenticated) {
      if (isAuthenticated) {
        _status = AuthStatus.authenticated;
      } else {
        _status = AuthStatus.unauthenticated;
        _currentUser = null;
      }
      notifyListeners();
    });
  }

  // Getters
  AuthStatus get status => _status;
  UserModel? get currentUser => _currentUser;
  String? get errorMessage => _errorMessage;
  bool get isAuthenticated => _status == AuthStatus.authenticated;
  bool get isEmailVerified => _isEmailVerified;

  // Initialiser l'état d'authentification
  Future<void> _initAuth() async {
    try {
      final isAuthenticated = await _authRepository.initAuth();

      if (isAuthenticated) {
        _status = AuthStatus.authenticated;
        // Charger les données utilisateur
        // Cela pourrait être fait en appelant un service utilisateur
      } else {
        _status = AuthStatus.unauthenticated;
      }
    } catch (e) {
      _status = AuthStatus.error;
      _errorMessage = e.toString();
    }

    notifyListeners();
  }

  // Inscription
  Future<bool> register({
    required String email,
    required String password,
    required String username,
    String? firstName,
    String? lastName,
  }) async {
    _status = AuthStatus.authenticating;
    _errorMessage = null;
    notifyListeners();

    try {
      _currentUser = await _authRepository.register(
        email: email,
        password: password,
        username: username,
        firstName: firstName,
        lastName: lastName,
      );

      _status = AuthStatus.authenticated;
      _isEmailVerified = _currentUser?.isVerified ?? false;

      notifyListeners();
      return true;
    } catch (e) {
      _status = AuthStatus.error;
      _errorMessage = e is AuthException ? e.message : e.toString();

      notifyListeners();
      return false;
    }
  }

  // Connexion
  Future<bool> login(String email, String password) async {
    _status = AuthStatus.authenticating;
    _errorMessage = null;
    notifyListeners();

    try {
      _currentUser = await _authRepository.login(email, password);

      _status = AuthStatus.authenticated;
      _isEmailVerified = _currentUser?.isVerified ?? false;

      notifyListeners();
      return true;
    } catch (e) {
      _status = AuthStatus.error;
      _errorMessage = e is AuthException ? e.message : e.toString();

      notifyListeners();
      return false;
    }
  }

  // Connexion avec Google
  Future<bool> loginWithGoogle() async {
    _status = AuthStatus.authenticating;
    _errorMessage = null;
    notifyListeners();

    try {
      _currentUser = await _authRepository.loginWithGoogle();

      _status = AuthStatus.authenticated;
      _isEmailVerified = _currentUser?.isVerified ?? false;

      notifyListeners();
      return true;
    } catch (e) {
      _status = AuthStatus.error;
      _errorMessage = e is AuthException ? e.message : e.toString();

      notifyListeners();
      return false;
    }
  }

  // Déconnexion
  Future<bool> logout() async {
    try {
      await _authRepository.logout();

      _status = AuthStatus.unauthenticated;
      _currentUser = null;
      _errorMessage = null;

      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = e is AuthException ? e.message : e.toString();

      notifyListeners();
      return false;
    }
  }

  // Envoyer un email de vérification
  Future<bool> sendEmailVerification() async {
    try {
      await _authRepository.sendEmailVerification();
      return true;
    } catch (e) {
      _errorMessage = e is AuthException ? e.message : e.toString();
      notifyListeners();
      return false;
    }
  }

  // Vérifier un email
  Future<bool> verifyEmail(String token) async {
    try {
      final result = await _authRepository.verifyEmail(token);

      if (result) {
        _isEmailVerified = true;

        // Mettre à jour le modèle utilisateur
        if (_currentUser != null) {
          _currentUser = _currentUser!.copyWith(isVerified: true);
        }

        notifyListeners();
      }

      return result;
    } catch (e) {
      _errorMessage = e is AuthException ? e.message : e.toString();
      notifyListeners();
      return false;
    }
  }

  // Demander une réinitialisation de mot de passe
  Future<bool> forgotPassword(String email) async {
    try {
      return await _authRepository.forgotPassword(email);
    } catch (e) {
      _errorMessage = e is AuthException ? e.message : e.toString();
      notifyListeners();
      return false;
    }
  }

  // Réinitialiser le mot de passe
  Future<bool> resetPassword(String token, String newPassword) async {
    try {
      return await _authRepository.resetPassword(token, newPassword);
    } catch (e) {
      _errorMessage = e is AuthException ? e.message : e.toString();
      notifyListeners();
      return false;
    }
  }

  // Vérifier un numéro de téléphone
  Future<void> verifyPhoneNumber({
    required String phoneNumber,
    required Function(String, int?) onCodeSent,
    required Function(String) onVerificationCompleted,
    required Function(String) onVerificationFailed,
    required Function() onCodeAutoRetrievalTimeout,
  }) async {
    try {
      await _authRepository.verifyPhoneNumber(
        phoneNumber: phoneNumber,
        onCodeSent: onCodeSent,
        onVerificationCompleted: onVerificationCompleted,
        onVerificationFailed: (error) {
          _errorMessage = error;
          notifyListeners();
          onVerificationFailed(error);
        },
        onCodeAutoRetrievalTimeout: onCodeAutoRetrievalTimeout,
      );
    } catch (e) {
      _errorMessage = e is AuthException ? e.message : e.toString();
      notifyListeners();
      onVerificationFailed(_errorMessage!);
    }
  }

  // Vérifier un code OTP
  Future<bool> verifyOtp(String verificationId, String smsCode) async {
    try {
      return await _authRepository.verifyOtp(verificationId, smsCode);
    } catch (e) {
      _errorMessage = e is AuthException ? e.message : e.toString();
      notifyListeners();
      return false;
    }
  }

  // Mettre à jour le modèle utilisateur
  void updateUser(UserModel user) {
    _currentUser = user;
    _isEmailVerified = user.isVerified;
    notifyListeners();
  }

  // Effacer les erreurs
  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }
}