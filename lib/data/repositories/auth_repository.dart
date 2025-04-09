import 'package:smart_turf/core/exceptions/auth_exception.dart';
import 'package:smart_turf/data/models/auth_token_model.dart';
import 'package:smart_turf/data/models/user_model.dart';
import 'package:smart_turf/services/api/auth_api_service.dart';
import 'package:smart_turf/services/firebase/firebase_auth_service.dart';
import 'package:smart_turf/services/local/session_manager.dart';

class AuthRepository {
  final AuthApiService _authApiService;
  final FirebaseAuthService _firebaseAuthService;
  final SessionManager _sessionManager;

  AuthRepository(
      this._authApiService,
      this._firebaseAuthService,
      this._sessionManager,
      );

  // Vérifier si l'utilisateur est connecté
  bool get isLoggedIn => _sessionManager.isSessionActive;

  // Stream pour l'état de la session
  Stream<bool> get authStateChanges => _sessionManager.sessionState;

  // Inscription avec email/mot de passe
  Future<UserModel> register({
    required String email,
    required String password,
    required String username,
    String? firstName,
    String? lastName,
  }) async {
    try {
      // Inscription dans Firebase
      final firebaseCredential = await _firebaseAuthService.signUpWithEmailAndPassword(
        email,
        password,
      );

      // Obtenir le token Firebase
      final firebaseToken = await firebaseCredential.user?.getIdToken();

      if (firebaseToken == null) {
        throw AuthException(message: 'Impossible d\'obtenir le token Firebase');
      }

      // Inscription dans le backend
      final authTokens = await _authApiService.firebaseAuth(firebaseToken);

      // Créer la session
      await _sessionManager.createSession(authTokens);

      // Renvoyer un modèle d'utilisateur (à remplacer par une vraie requête API)
      return UserModel(
        id: int.parse(authTokens.userId ?? '0'),
        email: email,
        username: username,
        firstName: firstName,
        lastName: lastName,
        isActive: true,
        isAdmin: false,
        isVerified: false,
        subscriptionLevel: 'free',
      );
    } catch (e) {
      if (e is AuthException) {
        rethrow;
      }
      throw AuthException(message: e.toString());
    }
  }

  // Connexion avec email/mot de passe
  Future<UserModel> login(String email, String password) async {
    try {
      // Connexion dans Firebase
      final firebaseCredential = await _firebaseAuthService.signInWithEmailAndPassword(
        email,
        password,
      );

      // Obtenir le token Firebase
      final firebaseToken = await firebaseCredential.user?.getIdToken();

      if (firebaseToken == null) {
        throw AuthException(message: 'Impossible d\'obtenir le token Firebase');
      }

      // Connexion dans le backend
      final authTokens = await _authApiService.firebaseAuth(firebaseToken);

      // Créer la session
      await _sessionManager.createSession(authTokens);

      // Renvoyer un modèle d'utilisateur (à remplacer par une vraie requête API)
      return UserModel(
        id: int.parse(authTokens.userId ?? '0'),
        email: email,
        username: email.split('@')[0], // Temporaire
        isActive: true,
        isAdmin: false,
        isVerified: true,
        subscriptionLevel: 'free',
      );
    } catch (e) {
      if (e is AuthException) {
        rethrow;
      }
      throw AuthException(message: e.toString());
    }
  }

  // Connexion avec Google
// Connexion avec Google
  Future<UserModel> loginWithGoogle() async {
    try {
      // Connexion dans Firebase
      final firebaseCredential = await _firebaseAuthService.signInWithGoogle();

      // Obtenir le token Firebase
      final firebaseToken = await firebaseCredential.user?.getIdToken();

      if (firebaseToken == null) {
        throw AuthException(message: 'Impossible d\'obtenir le token Firebase');
      }

      // Connexion dans le backend
      final authTokens = await _authApiService.firebaseAuth(firebaseToken);

      // Créer la session
      await _sessionManager.createSession(authTokens);

      // Renvoyer un modèle d'utilisateur (à remplacer par une vraie requête API)
      final user = firebaseCredential.user!;

      return UserModel(
        id: int.parse(authTokens.userId ?? '0'),
        email: user.email ?? '',
        username: user.displayName ?? user.email?.split('@')[0] ?? '',
        firstName: user.displayName?.split(' ').first ?? '',
        lastName: (user.displayName?.split(' ').length ?? 0) > 1
            ? user.displayName?.split(' ').skip(1).join(' ')
            : '',
        profilePicture: user.photoURL ?? '',
        isActive: true,
        isAdmin: false,
        isVerified: user.emailVerified,
        subscriptionLevel: 'free',
      );
    } catch (e) {
      if (e is AuthException) {
        rethrow;
      }
      throw AuthException(message: e.toString());
    }
  }

  // Déconnexion
  Future<void> logout() async {
    try {
      await _firebaseAuthService.signOut();
      await _sessionManager.endSession();
    } catch (e) {
      throw AuthException(message: e.toString());
    }
  }

  // Envoyer un email de vérification
  Future<void> sendEmailVerification() async {
    try {
      await _firebaseAuthService.sendEmailVerification();
    } catch (e) {
      if (e is AuthException) {
        rethrow;
      }
      throw AuthException(message: e.toString());
    }
  }

  // Vérifier un email
  Future<bool> verifyEmail(String token) async {
    try {
      return await _authApiService.verifyEmail(token);
    } catch (e) {
      if (e is AuthException) {
        rethrow;
      }
      throw AuthException(message: e.toString());
    }
  }

  // Demander une réinitialisation de mot de passe
  Future<bool> forgotPassword(String email) async {
    try {
      await _firebaseAuthService.sendPasswordResetEmail(email);
      return await _authApiService.forgotPassword(email);
    } catch (e) {
      if (e is AuthException) {
        rethrow;
      }
      throw AuthException(message: e.toString());
    }
  }

  // Réinitialiser le mot de passe
  Future<bool> resetPassword(String token, String newPassword) async {
    try {
      return await _authApiService.resetPassword(token, newPassword);
    } catch (e) {
      if (e is AuthException) {
        rethrow;
      }
      throw AuthException(message: e.toString());
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
      await _firebaseAuthService.verifyPhoneNumber(
        phoneNumber: phoneNumber,
        verificationCompleted: (credential) {
          onVerificationCompleted('Vérification automatique réussie');
        },
        verificationFailed: (error) {
          onVerificationFailed(error.message ?? 'Une erreur inconnue est survenue');
        },
        codeSent: onCodeSent,
        codeAutoRetrievalTimeout: (_) {
          onCodeAutoRetrievalTimeout();
        },
      );
    } catch (e) {
      throw AuthException(message: e.toString());
    }
  }


  // Vérifier un code OTP
  Future<bool> verifyOtp(String verificationId, String smsCode) async {
    try {
      await _firebaseAuthService.verifyOtp(verificationId, smsCode);
      return true;
    } catch (e) {
      if (e is AuthException) {
        rethrow;
      }
      throw AuthException(message: e.toString());
    }
  }

  // Initialiser l'état d'authentification
  Future<bool> initAuth() async {
    return await _sessionManager.initSession();
  }
}