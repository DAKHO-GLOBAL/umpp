class ApiConfig {
  // Base URL - Changez ceci selon votre environnement
  static const String baseUrl = 'http://192.168.1.80:5000/api';

  // Endpoints d'authentification
  static const String loginEndpoint = '$baseUrl/auth/login';
  static const String registerEndpoint = '$baseUrl/auth/register';
  static const String refreshTokenEndpoint = '$baseUrl/auth/refresh';
  static const String forgotPasswordEndpoint = '$baseUrl/auth/forgot-password';

  // Endpoints utilisateur
  static const String userProfileEndpoint = '$baseUrl/users/profile';

  // Endpoints pour les prédictions
  static const String upcomingRacesEndpoint = '$baseUrl/predictions/upcoming';
  static const String standardPredictionEndpoint = '$baseUrl/predictions/standard';
  static const String top3PredictionEndpoint = '$baseUrl/predictions/top3';
  static const String top7PredictionEndpoint = '$baseUrl/predictions/top7';

  // Endpoints pour les simulations
  static const String basicSimulationEndpoint = '$baseUrl/simulations/basic';
  static const String advancedSimulationEndpoint = '$baseUrl/simulations/advanced';
}

class AppConfig {
  static const String appName = 'SmartTurf';
  static const String tokenKey = 'auth_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String userKey = 'user_data';
}