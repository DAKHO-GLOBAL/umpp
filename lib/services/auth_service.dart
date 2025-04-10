import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:smart_turf/config/api_config.dart';
import 'package:smart_turf/models/auth_response.dart';
import 'package:smart_turf/models/user.dart';
import 'package:smart_turf/services/storage_service.dart';

class AuthService {
  final StorageService _storage = StorageService();

  // Méthode de connexion
  Future<AuthResponse> login(String email, String password) async {
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

      final responseData = jsonDecode(response.body);

      if (response.statusCode == 200 && responseData['success'] == true) {
        final authResponse = AuthResponse.fromJson(responseData);

        if (authResponse.accessToken != null) {
          await _storage.write(key: AppConfig.tokenKey, value: authResponse.accessToken!);
        }

        if (authResponse.refreshToken != null) {
          await _storage.write(key: AppConfig.refreshTokenKey, value: authResponse.refreshToken!);
        }

        if (authResponse.user != null) {
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString(AppConfig.userKey, jsonEncode(authResponse.user!.toJson()));
        }

        return authResponse;
      } else {
        return AuthResponse.error(responseData['message'] ?? 'Login failed');
      }
    } catch (e) {
      return AuthResponse.error('Network error: ${e.toString()}');
    }
  }

  // Méthode d'inscription
  Future<AuthResponse> register(
      String email,
      String username,
      String password,
      String confirmPassword, {
        String? firstName,
        String? lastName,
      }) async {
    try {
      final response = await http.post(
        Uri.parse(ApiConfig.registerEndpoint),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'email': email,
          'username': username,
          'password': password,
          'confirm_password': confirmPassword,
          'first_name': firstName,
          'last_name': lastName,
        }),
      );

      final responseData = jsonDecode(response.body);

      if (response.statusCode == 201 && responseData['success'] == true) {
        final authResponse = AuthResponse.fromJson(responseData);

        if (authResponse.accessToken != null) {
          await _storage.write(key: AppConfig.tokenKey, value: authResponse.accessToken!);
        }

        if (authResponse.refreshToken != null) {
          await _storage.write(key: AppConfig.refreshTokenKey, value: authResponse.refreshToken!);
        }

        if (authResponse.user != null) {
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString(AppConfig.userKey, jsonEncode(authResponse.user!.toJson()));
        }

        return authResponse;
      } else {
        String errorMessage = responseData['message'] ?? 'Registration failed';
        if (responseData['errors'] != null) {
          errorMessage = responseData['errors'].values.join(', ');
        }
        return AuthResponse.error(errorMessage);
      }
    } catch (e) {
      return AuthResponse.error('Network error: ${e.toString()}');
    }
  }

  // Récupérer l'utilisateur connecté
  Future<User?> getCurrentUser() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final userData = prefs.getString(AppConfig.userKey);

      if (userData != null) {
        return User.fromJson(jsonDecode(userData));
      }
      return null;
    } catch (e) {
      print('Error retrieving user: ${e.toString()}');
      return null;
    }
  }

  // Vérifier si l'utilisateur est connecté
  Future<bool> isLoggedIn() async {
    try {
      final token = await _storage.read(key: AppConfig.tokenKey);
      return token != null;
    } catch (e) {
      return false;
    }
  }

  // Méthode de déconnexion
  Future<void> logout() async {
    try {
      await _storage.delete(key: AppConfig.tokenKey);
      await _storage.delete(key: AppConfig.refreshTokenKey);

      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(AppConfig.userKey);
    } catch (e) {
      print('Error during logout: ${e.toString()}');
    }
  }

  // Récupérer le token
  Future<String?> getToken() async {
    return await _storage.read(key: AppConfig.tokenKey);
  }

  // Rafraîchir le token
  Future<String?> refreshTokenIfNeeded() async {
    try {
      final currentToken = await _storage.read(key: AppConfig.tokenKey);
      final refreshToken = await _storage.read(key: AppConfig.refreshTokenKey);

      if (currentToken == null || refreshToken == null) {
        return null;
      }

      final response = await http.post(
        Uri.parse(ApiConfig.refreshTokenEndpoint),
        headers: {
          'Authorization': 'Bearer $refreshToken',
        },
      );

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        final newToken = responseData['access_token'];

        if (newToken != null) {
          await _storage.write(key: AppConfig.tokenKey, value: newToken);
          return newToken;
        }
      }

      return currentToken;
    } catch (e) {
      print('Error refreshing token: ${e.toString()}');
      return null;
    }
  }

  // Réinitialiser le mot de passe
  Future<AuthResponse> forgotPassword(String email) async {
    try {
      final response = await http.post(
        Uri.parse(ApiConfig.forgotPasswordEndpoint),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'email': email,
        }),
      );

      final responseData = jsonDecode(response.body);

      if (response.statusCode == 200 && responseData['success'] == true) {
        return AuthResponse(
          success: true,
          message: responseData['message'] ?? 'Password reset email sent',
        );
      } else {
        return AuthResponse.error(responseData['message'] ?? 'Password reset failed');
      }
    } catch (e) {
      return AuthResponse.error('Network error: ${e.toString()}');
    }
  }
}
