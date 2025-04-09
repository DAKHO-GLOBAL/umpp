class ApiEndpoints {
  // Endpoints d'authentification
  static const String login = '/auth/login';
  static const String register = '/auth/register';
  static const String refreshToken = '/auth/refresh';
  static const String forgotPassword = '/auth/forgot-password';
  static const String resetPassword = '/auth/reset-password';
  static const String verifyEmail = '/auth/verify-email';
  static const String verifyPhone = '/auth/verify-phone';
  static const String firebaseAuth = '/auth/firebase-auth';

  // Endpoints utilisateur
  static const String profile = '/users/profile';
  static const String changePassword = '/users/password';
  static const String preferences = '/users/preferences';
  static const String statistics = '/users/statistics';
  static const String subscription = '/users/subscription';
  static const String notificationSettings = '/users/notification-settings';

  // Endpoints de courses
  static const String upcomingCourses = '/courses/upcoming';
  static const String courseDetails = '/courses/'; // + course_id
  static const String courseParticipants = '/courses/'; // + course_id + '/participants'
  static const String courseOdds = '/courses/'; // + course_id + '/odds'
  static const String courseResults = '/courses/'; // + course_id + '/results'

  // Endpoints de prédictions
  static const String standardPrediction = '/predictions/standard/'; // + course_id
  static const String top3Prediction = '/predictions/top3/'; // + course_id
  static const String top7Prediction = '/predictions/top7/'; // + course_id
  static const String predictionHistory = '/predictions/history';

  // Endpoints de simulations
  static const String basicSimulation = '/simulations/basic/'; // + course_id
  static const String advancedSimulation = '/simulations/advanced/'; // + course_id
  static const String simulationHistory = '/simulations/history';

  // Endpoints d'abonnement
  static const String subscriptionPlans = '/subscriptions/plans';
  static const String subscribe = '/subscriptions/subscribe';
  static const String cancelSubscription = '/subscriptions/cancel';
  static const String verifyPayment = '/subscriptions/verify-payment';
  static const String promoCode = '/subscriptions/check-promo';

  // Endpoints de notifications
  static const String notifications = '/notifications';
  static const String markAsRead = '/notifications/'; // + notification_id + '/read'
  static const String markAllAsRead = '/notifications/mark-all-read';
  static const String registerDevice = '/notifications/register-device';
}