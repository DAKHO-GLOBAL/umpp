import 'package:smart_turf/core/constants/api_constants.dart';
import 'package:smart_turf/core/exceptions/api_exception.dart';
import 'package:smart_turf/data/models/user_model.dart';
import 'package:smart_turf/services/api/api_client.dart';
import 'package:smart_turf/services/local/storage_service.dart';

class UserRepository {
  final ApiClient _apiClient;
  final StorageService _storageService;

  UserRepository(this._apiClient, this._storageService);

  // Obtenir le profil de l'utilisateur
  Future<UserModel> getUserProfile() async {
    try {
      final response = await _apiClient.get(ApiEndpoints.profile);

      if (response['success']) {
        final userModel = UserModel.fromJson(response['data']);

        // Mettre en cache les données utilisateur
        await _storageService.saveUserData(userModel.toJson());

        return userModel;
      } else {
        throw ApiException(message: response['message'] ?? 'Échec de récupération du profil');
      }
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException(message: e.toString());
    }
  }

  // Mettre à jour le profil de l'utilisateur
  Future<UserModel> updateProfile({
    String? firstName,
    String? lastName,
    String? username,
    String? bio,
  }) async {
    try {
      final data = <String, dynamic>{};

      if (firstName != null) data['first_name'] = firstName;
      if (lastName != null) data['last_name'] = lastName;
      if (username != null) data['username'] = username;
      if (bio != null) data['bio'] = bio;

      final response = await _apiClient.put(
        ApiEndpoints.profile,
        data: data,
      );

      if (response['success']) {
        final updatedUser = UserModel.fromJson(response['data']);

        // Mettre à jour le cache
        await _storageService.saveUserData(updatedUser.toJson());

        return updatedUser;
      } else {
        throw ApiException(message: response['message'] ?? 'Échec de mise à jour du profil');
      }
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException(message: e.toString());
    }
  }

  // Changer le mot de passe
  Future<bool> changePassword(String currentPassword, String newPassword) async {
    try {
      final response = await _apiClient.put(
        ApiEndpoints.changePassword,
        data: {
          'current_password': currentPassword,
          'new_password': newPassword,
          'confirm_password': newPassword,
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

  // Mettre à jour les préférences utilisateur
  Future<Map<String, dynamic>> updatePreferences(Map<String, dynamic> preferences) async {
    try {
      final response = await _apiClient.put(
        ApiEndpoints.preferences,
        data: preferences,
      );

      if (response['success']) {
        // Mettre à jour le cache des préférences
        await _storageService.savePreferences(response['data']);

        return response['data'];
      } else {
        throw ApiException(message: response['message'] ?? 'Échec de mise à jour des préférences');
      }
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException(message: e.toString());
    }
  }

  // Obtenir les préférences utilisateur
  Future<Map<String, dynamic>> getPreferences() async {
    try {
      // Essayer de récupérer depuis le cache d'abord
      final cachedPreferences = _storageService.getPreferences();
      if (cachedPreferences != null) {
        return cachedPreferences;
      }

      // Sinon, récupérer depuis l'API
      final response = await _apiClient.get(ApiEndpoints.preferences);

      if (response['success']) {
        // Mettre en cache les préférences
        await _storageService.savePreferences(response['data']);

        return response['data'];
      } else {
        throw ApiException(message: response['message'] ?? 'Échec de récupération des préférences');
      }
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException(message: e.toString());
    }
  }

  // Obtenir les statistiques utilisateur
  Future<Map<String, dynamic>> getStatistics() async {
    try {
      final response = await _apiClient.get(ApiEndpoints.statistics);

      if (response['success']) {
        return response['data'];
      } else {
        throw ApiException(message: response['message'] ?? 'Échec de récupération des statistiques');
      }
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException(message: e.toString());
    }
  }

  // Mettre à jour les paramètres de notification
  Future<Map<String, dynamic>> updateNotificationSettings(Map<String, dynamic> settings) async {
    try {
      final response = await _apiClient.put(
        ApiEndpoints.notificationSettings,
        data: settings,
      );

      if (response['success']) {
        return response['data'];
      } else {
        throw ApiException(message: response['message'] ?? 'Échec de mise à jour des paramètres de notification');
      }
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException(message: e.toString());
    }
  }
  // Obtenir les paramètres de notification
  Future<Map<String, dynamic>> getNotificationSettings() async {
    try {
      final response = await _apiClient.get(ApiEndpoints.notificationSettings);

      if (response['success']) {
        return response['data'];
      } else {
        throw ApiException(message: response['message'] ?? 'Échec de récupération des paramètres de notification');
      }
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException(message: e.toString());
    }
  }

  // Obtenir les informations d'abonnement
  Future<Map<String, dynamic>> getSubscriptionInfo() async {
    try {
      final response = await _apiClient.get(ApiEndpoints.subscription);

      if (response['success']) {
        return response['data'];
      } else {
        throw ApiException(message: response['message'] ?? 'Échec de récupération des informations d\'abonnement');
      }
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException(message: e.toString());
    }
  }

  // Désactiver le compte utilisateur
  Future<bool> deactivateAccount(String password) async {
    try {
      final response = await _apiClient.post(
        '/users/deactivate',
        data: {
          'password': password,
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

  // Mettre à jour l'image de profil
  Future<String> updateProfilePicture(String filePath) async {
    try {
      // Note: Cette méthode nécessiterait une implémentation spécifique pour le téléchargement de fichiers
      // Utilisation d'un FormData avec Dio par exemple
      final response = await _apiClient.post(
        '/users/profile-picture',
        data: {
          'file_path': filePath,
        },
      );

      if (response['success']) {
        final pictureUrl = response['data']['url'];

        // Mettre à jour le cache
        final userData = _storageService.getUserData();
        if (userData != null) {
          userData['profile_picture'] = pictureUrl;
          await _storageService.saveUserData(userData);
        }

        return pictureUrl;
      } else {
        throw ApiException(message: response['message'] ?? 'Échec de mise à jour de l\'image de profil');
      }
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException(message: e.toString());
    }
  }

  // Récupérer le nom d'utilisateur
  Future<String?> getUsername() async {
    try {
      // Essayer de récupérer depuis le cache d'abord
      final userData = _storageService.getUserData();
      if (userData != null && userData.containsKey('username')) {
        return userData['username'];
      }

      // Sinon, récupérer depuis l'API
      final response = await _apiClient.get('/users/username');

      if (response['success']) {
        return response['data']['username'];
      } else {
        throw ApiException(message: response['message'] ?? 'Échec de récupération du nom d\'utilisateur');
      }
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException(message: e.toString());
      return null;
    }
  }
}