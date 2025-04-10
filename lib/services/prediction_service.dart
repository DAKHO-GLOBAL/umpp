import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:smart_turf/config/api_config.dart';
import 'package:smart_turf/models/prediction.dart';
import 'package:smart_turf/models/api_response.dart';
import 'package:smart_turf/services/auth_service.dart';

class PredictionService {
  final AuthService _authService = AuthService();

  /// Récupère les prédictions standard pour une course donnée
  Future<ApiResponse<Prediction>> getStandardPrediction(int courseId) async {
    try {
      final token = await _authService.getToken();

      if (token == null) {
        return ApiResponse.error('Vous devez être connecté pour accéder aux prédictions');
      }

      final response = await http.get(
        Uri.parse('${ApiConfig.standardPredictionEndpoint}/$courseId'),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      final responseData = jsonDecode(response.body);

      if (response.statusCode == 200 && responseData['success'] == true) {
        final prediction = Prediction.fromJson(responseData);
        return ApiResponse<Prediction>(
          success: true,
          message: 'Prédiction récupérée avec succès',
          data: prediction,
        );
      } else {
        return ApiResponse.error(responseData['message'] ?? 'Erreur lors de la récupération de la prédiction');
      }
    } catch (e) {
      return ApiResponse.error('Erreur de connexion: ${e.toString()}');
    }
  }

  /// Récupère les prédictions Top 3 pour une course donnée
  Future<ApiResponse<Prediction>> getTop3Prediction(int courseId) async {
    try {
      final token = await _authService.getToken();

      if (token == null) {
        return ApiResponse.error('Vous devez être connecté pour accéder aux prédictions');
      }

      final response = await http.get(
        Uri.parse('${ApiConfig.top3PredictionEndpoint}/$courseId'),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      final responseData = jsonDecode(response.body);

      if (response.statusCode == 200 && responseData['success'] == true) {
        final prediction = Prediction.fromJson(responseData);
        return ApiResponse<Prediction>(
          success: true,
          message: 'Prédiction Top 3 récupérée avec succès',
          data: prediction,
        );
      } else {
        // Vérifier si c'est une erreur d'abonnement
        if (response.statusCode == 403 && responseData['message']?.contains('subscription') == true) {
          return ApiResponse.error('Votre abonnement ne permet pas d\'accéder aux prédictions Top 3');
        }

        return ApiResponse.error(responseData['message'] ?? 'Erreur lors de la récupération de la prédiction');
      }
    } catch (e) {
      return ApiResponse.error('Erreur de connexion: ${e.toString()}');
    }
  }

  /// Récupère les prédictions Top 7 pour une course donnée (premium)
  Future<ApiResponse<Prediction>> getTop7Prediction(int courseId) async {
    try {
      final token = await _authService.getToken();

      if (token == null) {
        return ApiResponse.error('Vous devez être connecté pour accéder aux prédictions');
      }

      final response = await http.get(
        Uri.parse('${ApiConfig.top7PredictionEndpoint}/$courseId'),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      final responseData = jsonDecode(response.body);

      if (response.statusCode == 200 && responseData['success'] == true) {
        final prediction = Prediction.fromJson(responseData);
        return ApiResponse<Prediction>(
          success: true,
          message: 'Prédiction Top 7 récupérée avec succès',
          data: prediction,
        );
      } else {
        // Vérifier si c'est une erreur d'abonnement
        if (response.statusCode == 403 && responseData['message']?.contains('subscription') == true) {
          return ApiResponse.error('Votre abonnement ne permet pas d\'accéder aux prédictions Top 7');
        }

        return ApiResponse.error(responseData['message'] ?? 'Erreur lors de la récupération de la prédiction');
      }
    } catch (e) {
      return ApiResponse.error('Erreur de connexion: ${e.toString()}');
    }
  }
}