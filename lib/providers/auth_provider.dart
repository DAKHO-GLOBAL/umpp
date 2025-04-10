import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:smart_turf/config/api_config.dart';
import 'package:smart_turf/models/auth_response.dart';
import 'package:smart_turf/models/user.dart';
import 'package:smart_turf/services/auth_service.dart';
import 'package:smart_turf/services/storage_service.dart';

class AuthProvider with ChangeNotifier {
  final AuthService _authService = AuthService();
  final StorageService _storage = StorageService();

  User? _user;
  bool _isLoading = false;
  String _errorMessage = '';
  bool _isAuthenticated = false;

  User? get user => _user;
  bool get isLoading => _isLoading;
  String get errorMessage => _errorMessage;
  bool get isAuthenticated => _isAuthenticated;

  AuthProvider() {
    _checkAuthStatus();
  }

  Future<void> _checkAuthStatus() async {
    _isLoading = true;
    notifyListeners();

    try {
      final isLoggedIn = await _authService.isLoggedIn();

      if (isLoggedIn) {
        _user = await _authService.getCurrentUser();
        _isAuthenticated = _user != null;
      } else {
        _isAuthenticated = false;
        _user = null;
      }
    } catch (e) {
      _errorMessage = e.toString();
      _isAuthenticated = false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> login(String email, String password) async {
    _isLoading = true;
    _errorMessage = '';
    notifyListeners();

    try {
      final response = await http.post(
        Uri.parse(ApiConfig.loginEndpoint),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'email': email,
          'password': password,
        }),
      );

      // Vérifiez d'abord si la réponse a un corps
      if (response.body.isEmpty) {
        _errorMessage = 'La réponse du serveur est vide';
        _isAuthenticated = false;
        notifyListeners();
        return false;
      }

      // Essayez de décoder la réponse JSON
      Map<String, dynamic> responseData;
      try {
        responseData = jsonDecode(response.body);
        print("Response data: $responseData"); // Log pour debug
      } catch (e) {
        _errorMessage = 'Erreur de décodage de la réponse: ${e.toString()}';
        _isAuthenticated = false;
        notifyListeners();
        return false;
      }

      if (response.statusCode == 200 && responseData['success'] == true) {
        // Vérifiez que tous les champs attendus sont présents
        final accessToken = responseData['access_token'];
        final refreshToken = responseData['refresh_token'];
        final userData = responseData['user'];

        if (accessToken == null) {
          _errorMessage = 'Le token d\'accès est manquant dans la réponse';
          _isAuthenticated = false;
          notifyListeners();
          return false;
        }

        // Stocker les tokens
        await _storage.write(key: AppConfig.tokenKey, value: accessToken);

        if (refreshToken != null) {
          await _storage.write(key: AppConfig.refreshTokenKey, value: refreshToken);
        }

        // Stocker et définir l'utilisateur
        if (userData != null) {
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString(AppConfig.userKey, jsonEncode(userData));

          try {
            // Construire un User à partir des données disponibles
            _user = User(
              id: userData['id'] ?? 0,
              email: userData['email'] ?? '',
              username: userData['username'] ?? userData['email'] ?? '',
              firstName: userData['first_name'] ?? userData['name']?.toString().split(' ').first,
              lastName: userData['last_name'],
              subscriptionLevel: userData['subscription_level'] ?? 'free',
              isActive: userData['is_active'] ?? true,
              isAdmin: userData['is_admin'] ?? false,
              isVerified: userData['is_verified'] ?? false,
            );

            _isAuthenticated = true;
            _errorMessage = '';
          } catch (e) {
            print("Erreur lors de la création de l'utilisateur: ${e.toString()}");
            _errorMessage = 'Erreur lors du traitement des données utilisateur';
            _isAuthenticated = false;
            notifyListeners();
            return false;
          }
        } else {
          _errorMessage = 'Données utilisateur manquantes dans la réponse';
          _isAuthenticated = false;
          notifyListeners();
          return false;
        }

        notifyListeners();
        return true;
      } else {
        _errorMessage = responseData['message'] ?? 'Échec de la connexion';
        _isAuthenticated = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      print("Erreur de connexion détaillée: ${e.toString()}");
      _errorMessage = 'Erreur de connexion: ${e.toString()}';
      _isAuthenticated = false;
      notifyListeners();
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Le reste des méthodes restent les mêmes mais doivent aussi utiliser _storage
  Future<bool> register(String email, String username, String password, String confirmPassword, {String? firstName, String? lastName}) async {
    _isLoading = true;
    _errorMessage = '';
    notifyListeners();

    try {
      final response = await _authService.register(
          email,
          username,
          password,
          confirmPassword,
          firstName: firstName,
          lastName: lastName
      );

      if (response.success && response.user != null) {
        _user = response.user;
        _isAuthenticated = true;
        _errorMessage = '';
        notifyListeners();
        return true;
      } else {
        _errorMessage = response.message;
        _isAuthenticated = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _errorMessage = e.toString();
      _isAuthenticated = false;
      notifyListeners();
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    _isLoading = true;
    notifyListeners();

    try {
      // Utilisez _storage au lieu de _authService.logout()
      await _storage.delete(key: AppConfig.tokenKey);
      await _storage.delete(key: AppConfig.refreshTokenKey);

      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(AppConfig.userKey);

      _user = null;
      _isAuthenticated = false;
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> forgotPassword(String email) async {
    _isLoading = true;
    _errorMessage = '';
    notifyListeners();

    try {
      final response = await _authService.forgotPassword(email);

      if (response.success) {
        _errorMessage = '';
        notifyListeners();
        return true;
      } else {
        _errorMessage = response.message;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _errorMessage = e.toString();
      notifyListeners();
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}