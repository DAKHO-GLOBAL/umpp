class PaymentConfig {
  // Configuration Orange Money
  static const bool enableOrangeMoney = true;
  static const String orangeMoneyApiUrl = 'https://api.orangemoney.com/v1';
  static const String orangeMoneyMerchantId = 'YOUR_MERCHANT_ID';
  static const String orangeMoneyApiKey = 'YOUR_API_KEY';
  static const int orangeMoneyApiTimeout = 30000; // millisecondes

  // Configuration pour les paiements par carte bancaire
  static const bool enableCardPayment = true;
  static const String stripePublishableKey = 'YOUR_STRIPE_PUBLISHABLE_KEY';
  static const String stripeSecretKey = 'YOUR_STRIPE_SECRET_KEY';

  // URL de rappel pour les paiements
  static const String paymentCallbackUrl = 'smartturf://payment-callback';

  // Durée d'une transaction en millisecondes
  static const int transactionTimeout = 300000; // 5 minutes

  // Délai de tentative avant retry en millisecondes
  static const int retryDelay = 5000; // 5 secondes

  // Nombre de tentatives maximum
  static const int maxRetryAttempts = 3;

  // Configuration des plans d'abonnement
  static const Map<String, Map<String, dynamic>> subscriptionPlans = {
    'standard': {
      'monthly_price': 9.99,
      'quarterly_price': 25.99,
      'yearly_price': 89.99,
      'trial_days': 7,
    },
    'premium': {
      'monthly_price': 19.99,
      'quarterly_price': 49.99,
      'yearly_price': 179.99,
      'trial_days': 7,
    }
  };

  // Pourcentages de réduction pour les codes promo
  static const Map<String, double> promoDiscounts = {
    'WELCOME': 0.20, // 20% de réduction
    'STUDENT': 0.30, // 30% de réduction
    'PREMIUM': 0.15, // 15% de réduction
  };
}