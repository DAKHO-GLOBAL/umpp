class ApiConfig {
  // URL de base de l'API
  static const String baseUrl = 'https://api.smartturf.com';

  // Endpoint API version
  static const String apiVersion = '/v1';

  // URL complète de l'API
  static String get apiUrl => '$baseUrl$apiVersion';

  // Headers par défaut
  static Map<String, String> get defaultHeaders => {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'x-app-version': '1.0.0',
  };

  // Configuration des timeouts (en millisecondes)
  static const int connectTimeout = 15000;
  static const int receiveTimeout = 15000;
  static const int sendTimeout = 15000;

  // Configuration de la politique de retry
  static const int maxRetryAttempts = 3;
  static const int retryDelay = 1000; // en millisecondes
}