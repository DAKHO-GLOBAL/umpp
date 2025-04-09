import 'dart:async';
import 'package:smart_turf/services/local/storage_service.dart';
import 'package:smart_turf/services/api/auth_api_service.dart';
import 'package:smart_turf/data/models/auth_token_model.dart';
import 'package:smart_turf/core/exceptions/auth_exception.dart';

class SessionManager {
  final StorageService _storageService;
  final AuthApiService _authApiService;

  // Délai avant d'essayer de rafraîchir le token (par défaut 5 minutes avant expiration)
  final Duration _refreshThreshold = const Duration(minutes: 5);

  // Timer pour le rafraîchissement automatique du token
  Timer? _refreshTimer;

  // Stream controller pour l'état de la session
  final _sessionController = StreamController<bool>.broadcast();

  // État actuel de la session
  bool _isSessionActive = false;

  SessionManager(this._storageService, this._authApiService);

  // Obtenir le stream de l'état de la session
  Stream<bool> get sessionState => _sessionController.stream;

  // Obtenir l'état actuel de la session
  bool get isSessionActive => _isSessionActive;

  // Initialiser la session
  Future<bool> initSession() async {
    final token = await _storageService.getAuthToken();

    if (token == null) {
      _isSessionActive = false;
      _sessionController.add(false);
      return false;
    }

    try {
      // Vérifier si le token est toujours valide et le rafraîchir si nécessaire
      await _checkAndRefreshToken();

      _isSessionActive = true;
      _sessionController.add(true);
      return true;
    } catch (e) {
      // Si le token est invalide ou ne peut pas être rafraîchi, effacer les données
      await _storageService.clearAuthData();
      _isSessionActive = false;
      _sessionController.add(false);
      return false;
    }
  }

  // Créer une nouvelle session (après connexion)
  Future<void> createSession(AuthTokenModel tokens) async {
    await _storageService.saveAuthToken(tokens.accessToken);
    await _storageService.saveRefreshToken(tokens.refreshToken);

    if (tokens.userId != null) {
      await _storageService.saveUserId(tokens.userId!);
    }

    // Configurer le timer pour le rafraîchissement automatique
    _setupRefreshTimer(tokens.expiresIn);

    _isSessionActive = true;
    _sessionController.add(true);
  }

  // Terminer la session (déconnexion)
  Future<void> endSession() async {
    await _storageService.clearAuthData();
    _refreshTimer?.cancel();

    _isSessionActive = false;
    _sessionController.add(false);
  }

  // Configurer le timer pour le rafraîchissement automatique du token
  void _setupRefreshTimer(int expiresIn) {
    _refreshTimer?.cancel();

    // Calculer le délai avant de rafraîchir le token
    final expiryDuration = Duration(seconds: expiresIn);
    final refreshDelay = expiryDuration - _refreshThreshold;

    // S'assurer que le délai est positif
    final delay = refreshDelay.isNegative ? Duration.zero : refreshDelay;

    _refreshTimer = Timer(delay, () async {
      await _refreshToken();
    });
  }

  // Vérifier et rafraîchir le token si nécessaire
  Future<void> _checkAndRefreshToken() async {
    final refreshToken = await _storageService.getRefreshToken();

    if (refreshToken == null) {
      throw AuthException(message: 'Refresh token not found');
    }

    try {
      final tokens = await _authApiService.refreshToken(refreshToken);
      await _storageService.saveAuthToken(tokens.accessToken);
      await _storageService.saveRefreshToken(tokens.refreshToken);

      // Reconfigurer le timer pour le prochain rafraîchissement
      _setupRefreshTimer(tokens.expiresIn);
    } catch (e) {
      // Si le rafraîchissement échoue, terminer la session
      await endSession();
      throw AuthException(message: 'Failed to refresh token');
    }
  }

  // Rafraîchir manuellement le token
  Future<void> _refreshToken() async {
    try {
      await _checkAndRefreshToken();
    } catch (e) {
      // Le rafraîchissement a échoué, la session est déjà terminée dans _checkAndRefreshToken
      print('Refresh token failed: $e');
    }
  }

  // Disposer les ressources lors de la destruction du service
  void dispose() {
    _refreshTimer?.cancel();
    _sessionController.close();
  }
}