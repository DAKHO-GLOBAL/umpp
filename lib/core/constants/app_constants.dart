class AppConstants {
  // Constantes générales de l'application
  static const String appName = 'SmartTurf';
  static const String appSlogan = 'Prédictions hippiques intelligentes';

  // Durées
  static const Duration animationDuration = Duration(milliseconds: 300);
  static const Duration splashScreenDuration = Duration(seconds: 2);

  // Valeurs par défaut
  static const int defaultPageSize = 20;
  static const int minSearchLength = 3;

  // Formats de dates
  static const String dateFormat = 'dd/MM/yyyy';
  static const String timeFormat = 'HH:mm';
  static const String dateTimeFormat = 'dd/MM/yyyy HH:mm';

  // Messages génériques
  static const String errorMessage = 'Une erreur est survenue. Veuillez réessayer.';
  static const String networkErrorMessage = 'Problème de connexion. Vérifiez votre réseau.';
  static const String sessionExpiredMessage = 'Votre session a expiré. Veuillez vous reconnecter.';
}