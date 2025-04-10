import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:smart_turf/config/api_config.dart';
import 'package:smart_turf/services/auth_service.dart';

class ApiService {
  final AuthService _authService = AuthService();

  // Méthode GET générique avec gestion de token
  Future<Map<String, dynamic>> get(String endpoint) async {
    try {
      // Vérifier et rafraîchir le token si nécessaire
      final token = await _authService.refreshTokenIfNeeded();

      if (token == null) {
        throw Exception('Not authenticated');
      }

      final response = await http.get(
        Uri.parse(endpoint),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return jsonDecode(response.body);
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['message'] ?? 'Request failed with status ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('API Error: ${e.toString()}');
    }
  }

  // Méthode POST générique avec gestion de token
  Future<Map<String, dynamic>> post(String endpoint, Map<String, dynamic> data) async {
    try {
      // Vérifier et rafraîchir le token si nécessaire
      final token = await _authService.refreshTokenIfNeeded();

      if (token == null) {
        throw Exception('Not authenticated');
      }

      final response = await http.post(
        Uri.parse(endpoint),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode(data),
      );

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return jsonDecode(response.body);
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['message'] ?? 'Request failed with status ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('API Error: ${e.toString()}');
    }
  }

  // Méthode PUT générique avec gestion de token
  Future<Map<String, dynamic>> put(String endpoint, Map<String, dynamic> data) async {
    try {
      // Vérifier et rafraîchir le token si nécessaire
      final token = await _authService.refreshTokenIfNeeded();

      if (token == null) {
        throw Exception('Not authenticated');
      }

      final response = await http.put(
        Uri.parse(endpoint),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode(data),
      );

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return jsonDecode(response.body);
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['message'] ?? 'Request failed with status ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('API Error: ${e.toString()}');
    }
  }

  // Récupérer les courses à venir
  Future<List<dynamic>> getUpcomingRaces() async {
    final response = await get(ApiConfig.upcomingRacesEndpoint);

    if (response['success'] == true && response['data'] != null) {
      return response['data'];
    } else {
      throw Exception('Failed to get upcoming races');
    }
  }

  // Obtenir une prédiction standard pour une course
  Future<Map<String, dynamic>> getStandardPrediction(int courseId) async {
    final endpoint = '${ApiConfig.standardPredictionEndpoint}/$courseId';
    final response = await get(endpoint);

    if (response['success'] == true && response['data'] != null) {
      return response;
    } else {
      throw Exception('Failed to get prediction');
    }
  }
}