import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:smart_turf/config/api_config.dart';
import 'package:smart_turf/models/race.dart';
import 'package:smart_turf/models/api_response.dart';
import 'package:smart_turf/services/auth_service.dart';

class RaceService {
  final AuthService _authService = AuthService();

  /// Récupère les courses à venir
  Future<ApiResponse<List<Race>>> getUpcomingRaces({int days = 1}) async {
    try {
      final token = await _authService.getToken();

      if (token == null) {
        return ApiResponse.error('Vous devez être connecté pour accéder aux courses');
      }

      final response = await http.get(
        Uri.parse('${ApiConfig.upcomingRacesEndpoint}?days=$days'),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      final responseData = jsonDecode(response.body);

      if (response.statusCode == 200 && responseData['success'] == true) {
        final List<Race> races = (responseData['data'] as List)
            .map((raceJson) => Race.fromJson(raceJson))
            .toList();

        return ApiResponse<List<Race>>(
          success: true,
          message: 'Courses récupérées avec succès',
          data: races,
        );
      } else {
        return ApiResponse.error(responseData['message'] ?? 'Erreur lors de la récupération des courses');
      }
    } catch (e) {
      return ApiResponse.error('Erreur de connexion: ${e.toString()}');
    }
  }

  /// Récupère les détails d'une course par son ID
  Future<ApiResponse<Race>> getRaceDetails(int raceId) async {
    try {
      final token = await _authService.getToken();

      if (token == null) {
        return ApiResponse.error('Vous devez être connecté pour accéder aux détails de la course');
      }

      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/courses/$raceId'),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      final responseData = jsonDecode(response.body);

      if (response.statusCode == 200 && responseData['success'] == true) {
        final race = Race.fromJson(responseData['data']);

        return ApiResponse<Race>(
          success: true,
          message: 'Détails de la course récupérés avec succès',
          data: race,
        );
      } else {
        return ApiResponse.error(responseData['message'] ?? 'Erreur lors de la récupération des détails de la course');
      }
    } catch (e) {
      return ApiResponse.error('Erreur de connexion: ${e.toString()}');
    }
  }

  /// Récupère les participants d'une course
  Future<ApiResponse<List<dynamic>>> getRaceParticipants(int raceId) async {
    try {
      final token = await _authService.getToken();

      if (token == null) {
        return ApiResponse.error('Vous devez être connecté pour accéder aux participants');
      }

      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/courses/$raceId/participants'),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      final responseData = jsonDecode(response.body);

      if (response.statusCode == 200 && responseData['success'] == true) {
        return ApiResponse<List<dynamic>>(
          success: true,
          message: 'Participants récupérés avec succès',
          data: responseData['data'],
        );
      } else {
        return ApiResponse.error(responseData['message'] ?? 'Erreur lors de la récupération des participants');
      }
    } catch (e) {
      return ApiResponse.error('Erreur de connexion: ${e.toString()}');
    }
  }

  /// Récupère les cotes d'une course
  Future<ApiResponse<Map<String, dynamic>>> getRaceOdds(int raceId) async {
    try {
      final token = await _authService.getToken();

      if (token == null) {
        return ApiResponse.error('Vous devez être connecté pour accéder aux cotes');
      }

      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/courses/$raceId/odds'),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      final responseData = jsonDecode(response.body);

      if (response.statusCode == 200 && responseData['success'] == true) {
        return ApiResponse<Map<String, dynamic>>(
          success: true,
          message: 'Cotes récupérées avec succès',
          data: {
            'timestamp': responseData['timestamp'],
            'odds': responseData['data'],
          },
        );
      } else {
        return ApiResponse.error(responseData['message'] ?? 'Erreur lors de la récupération des cotes');
      }
    } catch (e) {
      return ApiResponse.error('Erreur de connexion: ${e.toString()}');
    }
  }

  /// Recherche des courses selon divers critères
  Future<ApiResponse<List<Race>>> searchRaces({
    String? dateFrom,
    String? dateTo,
    String? hippodrome,
    String? courseType,
    int? horseId,
    int? jockeyId,
    int page = 1,
    int perPage = 20,
  }) async {
    try {
      final token = await _authService.getToken();

      if (token == null) {
        return ApiResponse.error('Vous devez être connecté pour effectuer une recherche');
      }

      // Construire l'URL avec les paramètres de recherche
      final queryParams = <String, String>{
        'page': page.toString(),
        'per_page': perPage.toString(),
      };

      if (dateFrom != null) queryParams['date_from'] = dateFrom;
      if (dateTo != null) queryParams['date_to'] = dateTo;
      if (hippodrome != null) queryParams['hippodrome'] = hippodrome;
      if (courseType != null) queryParams['type'] = courseType;
      if (horseId != null) queryParams['cheval_id'] = horseId.toString();
      if (jockeyId != null) queryParams['jockey_id'] = jockeyId.toString();

      final uri = Uri.parse('${ApiConfig.baseUrl}/courses/search').replace(queryParameters: queryParams);

      final response = await http.get(
        uri,
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      final responseData = jsonDecode(response.body);

      if (response.statusCode == 200 && responseData['success'] == true) {
        final List<Race> races = (responseData['data'] as List)
            .map((raceJson) => Race.fromJson(raceJson))
            .toList();

        return ApiResponse<List<Race>>(
          success: true,
          message: 'Recherche effectuée avec succès',
          data: races,
        );
      } else {
        return ApiResponse.error(responseData['message'] ?? 'Erreur lors de la recherche');
      }
    } catch (e) {
      return ApiResponse.error('Erreur de connexion: ${e.toString()}');
    }
  }
}