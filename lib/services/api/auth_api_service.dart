import 'package:smart_turf/core/constants/api_constants.dart';
import 'package:smart_turf/core/exceptions/api_exception.dart';
import 'package:smart_turf/services/api/api_client.dart';
import 'package:smart_turf/data/models/auth_token_model.dart';
import 'package:smart_turf/data/models/user_model.dart';

class AuthApiService {
  final ApiClient _apiClient;

  AuthApiService(this._apiClient);

  // Authentification avec email/mot de passe
  Future<AuthTokenModel> login(String email, String password) async {
    try {
      final response = await _apiClient.post(
        ApiEndpoints.login,
        data: {
          'email': email,
          'password': password,
        },
        requiresAuth: false,
      );

      if (response['success']) {
        return AuthTokenModel.fromJson(response);
      } else {
        throw ApiException(message: response['message'] ?? 'Échec de connexion');
      }
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException(message: e.toString());
    }
  }

  // Inscription d'un nouvel utilisateur
  Future<AuthTokenModel> register({
    required String email,
    required String password,
    required String username,
    String? firstName,
    String? lastName,
  }) async {
    try {
      final response = await _apiClient.post(
        ApiEndpoints.register,
        data: {
          'email': email,
          'password': password,
          'username': username,
          'first_name': firstName,
          'last_name': lastName,
        },
        requiresAuth: false,
      );

      if (response['success']) {
        return AuthTokenModel.fromJson(response);
      } else {
        throw ApiException(message: response['message'] ?? 'Échec d\'inscription');
      }
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException(message: e.toString());
    }
  }

  // Authentification avec token Firebase
  Future<AuthTokenModel> firebaseAuth(String firebaseToken) async {
    try {
      final response = await _apiClient.post(
        ApiEndpoints.firebaseAuth,
        data: {
          'firebase_token': firebaseToken,
        },
        requiresAuth: false,
      );

      if (response['success']) {
        return AuthTokenModel.fromJson(response);
      } else {
        throw ApiException(message: response['message'] ?? 'Échec d\'authentification Firebase');
      }
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException(message: e.toString());
    }
  }

  // Rafraîchir le token d'authentification
  Future<AuthTokenModel> refreshToken(String refreshToken) async {
    try {
      final response = await _apiClient.post(
        ApiEndpoints.refreshToken,
        data: {
          'refresh_token': refreshToken,
        },
        requiresAuth: false,
      );

      if (response['success']) {
        return AuthTokenModel.fromJson(response);
      } else {
        throw ApiException(message: response['message'] ?? 'Échec de rafraîchissement du token');
      }
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException(message: e.toString());
    }
  }

  // Demande de réinitialisation de mot de passe
  Future<bool> forgotPassword(String email) async {
    try {
      final response = await _apiClient.post(
        ApiEndpoints.forgotPassword,
        data: {
          'email': email,
        },
        requiresAuth: false,
      );

      return response['success'] ?? false;
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException(message: e.toString());
    }
  }

  // Réinitialisation de mot de passe
  Future<bool> resetPassword(String token, String newPassword) async {
    try {
      final response = await _apiClient.post(
        ApiEndpoints.resetPassword,
        data: {
          'token': token,
          'new_password': newPassword,
        },
        requiresAuth: false,
      );

      return response['success'] ?? false;
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException(message: e.toString());
    }
  }

  // Vérification d'email
  Future<bool> verifyEmail(String token) async {
    try {
      final response = await _apiClient.post(
        ApiEndpoints.verifyEmail,
        data: {
          'token': token,
        },
        requiresAuth: false,
      );

      return response['success'] ?? false;
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException(message: e.toString());
    }
  }

  // Vérification de téléphone via SMS
  Future<bool> verifyPhone(String phoneNumber, String code) async {
    try {
      final response = await _apiClient.post(
        ApiEndpoints.verifyPhone,
        data: {
          'phone_number': phoneNumber,
          'verification_code': code,
        },
      );

      return response['success'] ?? false;
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException(message: e.toString());
    }
  }
}