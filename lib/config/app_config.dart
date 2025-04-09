class AppConfig {
  // Version de l'application
  static const String appVersion = '1.0.0';

  // Configuration de l'environnement
  static const bool isDevelopment = true;

  // Timeout pour les requêtes API (en millisecondes)
  static const int apiTimeout = 30000;

  // Configuration des limites
  static const int maxLoginAttempts = 5;
  static const int otpResendDelay = 60; // en secondes

  // Niveaux d'abonnement
  static const Map<String, Map<String, dynamic>> subscriptionLevels = {
    'free': {
      'predictions_per_day': 5,
      'simulations_per_day': 2,
      'features': ['basic_predictions']
    },
    'standard': {
      'predictions_per_day': 30,
      'simulations_per_day': 15,
      'features': ['basic_predictions', 'top3_predictions', 'basic_simulations']
    },
    'premium': {
      'predictions_per_day': -1, // Illimité
      'simulations_per_day': -1, // Illimité
      'features': [
        'basic_predictions',
        'top3_predictions',
        'top7_predictions',
        'basic_simulations',
        'advanced_simulations',
        'notifications'
      ]
    }
  };
}