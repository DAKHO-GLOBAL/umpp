import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

// Service de stockage qui s'adapte à la plateforme
class StorageService {
  // Utiliser flutter_secure_storage pour mobile
  final FlutterSecureStorage? _secureStorage =
  !kIsWeb ? const FlutterSecureStorage() : null;

  // Méthode pour écrire des données
  Future<void> write({required String key, required String value}) async {
    if (kIsWeb) {
      // Pour le web, utiliser SharedPreferences
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(key, value);
    } else {
      // Pour mobile, utiliser SecureStorage
      await _secureStorage!.write(key: key, value: value);
    }
  }

  // Méthode pour lire des données
  Future<String?> read({required String key}) async {
    if (kIsWeb) {
      // Pour le web, utiliser SharedPreferences
      final prefs = await SharedPreferences.getInstance();
      return prefs.getString(key);
    } else {
      // Pour mobile, utiliser SecureStorage
      return await _secureStorage!.read(key: key);
    }
  }

  // Méthode pour supprimer des données
  Future<void> delete({required String key}) async {
    if (kIsWeb) {
      // Pour le web, utiliser SharedPreferences
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(key);
    } else {
      // Pour mobile, utiliser SecureStorage
      await _secureStorage!.delete(key: key);
    }
  }
}