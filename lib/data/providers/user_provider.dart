import 'package:flutter/foundation.dart';
import 'package:smart_turf/core/exceptions/api_exception.dart';
import 'package:smart_turf/data/models/user_model.dart';
import 'package:smart_turf/data/repositories/user_repository.dart';

enum UserDataStatus {
  initial,
  loading,
  loaded,
  error,
}

class UserProvider with ChangeNotifier {
  final UserRepository _userRepository;

  UserDataStatus _status = UserDataStatus.initial;
  UserModel? _user;
  String? _errorMessage;
  Map<String, dynamic>? _preferences;
  Map<String, dynamic>? _statistics;
  Map<String, dynamic>? _notificationSettings;
  Map<String, dynamic>? _subscriptionInfo;

  UserProvider({
    required UserRepository userRepository,
  }) : _userRepository = userRepository;

  // Getters
  UserDataStatus get status => _status;
  UserModel? get user => _user;
  String? get errorMessage => _errorMessage;
  Map<String, dynamic>? get preferences => _preferences;
  Map<String, dynamic>? get statistics => _statistics;
  Map<String, dynamic>? get notificationSettings => _notificationSettings;
  Map<String, dynamic>? get subscriptionInfo => _subscriptionInfo;

  // Charger le profil utilisateur
  Future<bool> loadUserProfile() async {
    _status = UserDataStatus.loading;
    _errorMessage = null;
    notifyListeners();

    try {
      _user = await _userRepository.getUserProfile();
      _status = UserDataStatus.loaded;
      notifyListeners();
      return true;
    } catch (e) {
      _status = UserDataStatus.error;
      _errorMessage = e is ApiException ? e.message : e.toString();
      notifyListeners();
      return false;
    }
  }

  // Mettre à jour le profil utilisateur
  Future<bool> updateProfile({
    String? firstName,
    String? lastName,
    String? username,
    String? bio,
  }) async {
    _status = UserDataStatus.loading;
    _errorMessage = null;
    notifyListeners();

    try {
      _user = await _userRepository.updateProfile(
        firstName: firstName,
        lastName: lastName,
        username: username,
        bio: bio,
      );

      _status = UserDataStatus.loaded;
      notifyListeners();
      return true;
    } catch (e) {
      _status = UserDataStatus.error;
      _errorMessage = e is ApiException ? e.message : e.toString();
      notifyListeners();
      return false;
    }
  }

  // Changer le mot de passe
  Future<bool> changePassword(String currentPassword, String newPassword) async {
    _errorMessage = null;
    notifyListeners();

    try {
      final result = await _userRepository.changePassword(currentPassword, newPassword);

      if (!result) {
        _errorMessage = 'Échec du changement de mot de passe';
        notifyListeners();
      }

      return result;
    } catch (e) {
      _errorMessage = e is ApiException ? e.message : e.toString();
      notifyListeners();
      return false;
    }
  }

  // Charger les préférences utilisateur
  Future<bool> loadPreferences() async {
    _errorMessage = null;
    notifyListeners();

    try {
      _preferences = await _userRepository.getPreferences();
      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = e is ApiException ? e.message : e.toString();
      notifyListeners();
      return false;
    }
  }

  // Mettre à jour les préférences utilisateur
  Future<bool> updatePreferences(Map<String, dynamic> preferences) async {
    _errorMessage = null;
    notifyListeners();

    try {
      _preferences = await _userRepository.updatePreferences(preferences);
      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = e is ApiException ? e.message : e.toString();
      notifyListeners();
      return false;
    }
  }

  // Charger les statistiques utilisateur
  Future<bool> loadStatistics() async {
    _errorMessage = null;
    notifyListeners();

    try {
      _statistics = await _userRepository.getStatistics();
      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = e is ApiException ? e.message : e.toString();
      notifyListeners();
      return false;
    }
  }

  // Charger les paramètres de notification
  Future<bool> loadNotificationSettings() async {
    _errorMessage = null;
    notifyListeners();

    try {
      _notificationSettings = await _userRepository.getNotificationSettings();
      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = e is ApiException ? e.message : e.toString();
      notifyListeners();
      return false;
    }
  }

  // Mettre à jour les paramètres de notification
  Future<bool> updateNotificationSettings(Map<String, dynamic> settings) async {
    _errorMessage = null;
    notifyListeners();

    try {
      _notificationSettings = await _userRepository.updateNotificationSettings(settings);
      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = e is ApiException ? e.message : e.toString();
      notifyListeners();
      return false;
    }
  }

  // Charger les informations d'abonnement
  Future<bool> loadSubscriptionInfo() async {
    _errorMessage = null;
    notifyListeners();

    try {
      _subscriptionInfo = await _userRepository.getSubscriptionInfo();
      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = e is ApiException ? e.message : e.toString();
      notifyListeners();
      return false;
    }
  }

  // Désactiver le compte utilisateur
  Future<bool> deactivateAccount(String password) async {
    _errorMessage = null;
    notifyListeners();

    try {
      final result = await _userRepository.deactivateAccount(password);

      if (!result) {
        _errorMessage = 'Échec de la désactivation du compte';
        notifyListeners();
      }

      return result;
    } catch (e) {
      _errorMessage = e is ApiException ? e.message : e.toString();
      notifyListeners();
      return false;
    }
  }

  // Mettre à jour l'image de profil
  Future<bool> updateProfilePicture(String filePath) async {
    _errorMessage = null;
    notifyListeners();

    try {
      final pictureUrl = await _userRepository.updateProfilePicture(filePath);

      // Mettre à jour le modèle utilisateur
      if (_user != null) {
        _user = _user!.copyWith(profilePicture: pictureUrl);
      }

      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = e is ApiException ? e.message : e.toString();
      notifyListeners();
      return false;
    }
  }

  // Effacer les erreurs
  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }
}