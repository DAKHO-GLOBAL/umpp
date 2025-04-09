import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

class StorageService {
  static final StorageService _instance = StorageService._internal();

  factory StorageService() {
    return _instance;
  }

  StorageService._internal();

  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();
  late SharedPreferences _preferences;

  // Clés pour le stockage sécurisé
  static const String _keyAuthToken = 'auth_token';
  static const String _keyRefreshToken = 'refresh_token';
  static const String _keyUserId = 'user_id';

  // Clés pour les préférences
  static const String _keyOnboardingCompleted = 'onboarding_completed';
  static const String _keyDarkMode = 'dark_mode';
  static const String _keyNotificationsEnabled = 'notifications_enabled';
  static const String _keyLanguage = 'language';

  // Initialiser les préférences partagées
  Future<void> initialize() async {
    _preferences = await SharedPreferences.getInstance();
  }
  // Méthodes pour le stockage sécurisé (tokens, identifiants)

  // Sauvegarder le token d'authentification
  Future<void> saveAuthToken(String token) async {
    await _secureStorage.write(key: _keyAuthToken, value: token);
  }

  // Récupérer le token d'authentification
  Future<String?> getAuthToken() async {
    return await _secureStorage.read(key: _keyAuthToken);
  }

  // Sauvegarder le token de rafraîchissement
  Future<void> saveRefreshToken(String token) async {
    await _secureStorage.write(key: _keyRefreshToken, value: token);
  }

  // Récupérer le token de rafraîchissement
  Future<String?> getRefreshToken() async {
    return await _secureStorage.read(key: _keyRefreshToken);
  }

  // Sauvegarder l'ID utilisateur
  Future<void> saveUserId(String userId) async {
    await _secureStorage.write(key: _keyUserId, value: userId);
  }

  // Récupérer l'ID utilisateur
  Future<String?> getUserId() async {
    return await _secureStorage.read(key: _keyUserId);
  }

  // Effacer toutes les données d'authentification (déconnexion)
  Future<void> clearAuthData() async {
    await _secureStorage.delete(key: _keyAuthToken);
    await _secureStorage.delete(key: _keyRefreshToken);
    await _secureStorage.delete(key: _keyUserId);
  }

  // Sauvegarder un objet utilisateur complet
  Future<void> saveUserData(Map<String, dynamic> userData) async {
    await _preferences.setString('user_data', jsonEncode(userData));
  }

  // Récupérer l'objet utilisateur
  Map<String, dynamic>? getUserData() {
    final String? userDataString = _preferences.getString('user_data');
    if (userDataString == null) {
      return null;
    }

    try {
      return jsonDecode(userDataString) as Map<String, dynamic>;
    } catch (e) {
      print('Erreur lors du décodage des données utilisateur: $e');
      return null;
    }
  }

  // Méthodes pour les préférences utilisateur

  // Vérifier si l'onboarding a été complété
  bool isOnboardingCompleted() {
    return _preferences.getBool(_keyOnboardingCompleted) ?? false;
  }

  // Marquer l'onboarding comme complété
  Future<void> setOnboardingCompleted(bool completed) async {
    await _preferences.setBool(_keyOnboardingCompleted, completed);
  }

  // Obtenir le mode sombre
  bool isDarkMode() {
    return _preferences.getBool(_keyDarkMode) ?? false;
  }

  // Définir le mode sombre
  Future<void> setDarkMode(bool enabled) async {
    await _preferences.setBool(_keyDarkMode, enabled);
  }

  // Vérifier si les notifications sont activées
  bool areNotificationsEnabled() {
    return _preferences.getBool(_keyNotificationsEnabled) ?? true;
  }

  // Activer/désactiver les notifications
  Future<void> setNotificationsEnabled(bool enabled) async {
    await _preferences.setBool(_keyNotificationsEnabled, enabled);
  }

  // Obtenir la langue
  String getLanguage() {
    return _preferences.getString(_keyLanguage) ?? 'fr';
  }

  // Définir la langue
  Future<void> setLanguage(String languageCode) async {
    await _preferences.setString(_keyLanguage, languageCode);
  }

  // Sauvegarder les préférences générales
  Future<void> savePreferences(Map<String, dynamic> preferences) async {
    await _preferences.setString('user_preferences', jsonEncode(preferences));
  }

  // Récupérer les préférences générales
  Map<String, dynamic>? getPreferences() {
    final String? preferencesString = _preferences.getString('user_preferences');
    if (preferencesString == null) {
      return null;
    }

    try {
      return jsonDecode(preferencesString) as Map<String, dynamic>;
    } catch (e) {
      print('Erreur lors du décodage des préférences: $e');
      return null;
    }
  }

  // Effacer toutes les données locales
  Future<void> clearAllData() async {
    await _secureStorage.deleteAll();
    await _preferences.clear();
  }
}