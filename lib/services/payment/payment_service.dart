import 'package:smart_turf/config/payment_config.dart';
import 'package:smart_turf/core/exceptions/payment_exception.dart';
import 'package:smart_turf/services/api/api_client.dart';

enum PaymentMethod {
  orangeMoney,
  creditCard,
  manual
}

enum PaymentStatus {
  initialized,
  pending,
  processing,
  completed,
  failed,
  cancelled,
  refunded
}

class PaymentService {
  static final PaymentService _instance = PaymentService._internal();
  final ApiClient _apiClient;

  factory PaymentService(ApiClient apiClient) {
    _instance._apiClient = apiClient;
    return _instance;
  }

  PaymentService._internal() : _apiClient = ApiClient(null);

  // Initialiser un paiement Orange Money
  Future<Map<String, dynamic>> initializeOrangeMoneyPayment({
    required String amount,
    required String currency,
    required String description,
    required String customerPhone,
    String? customerEmail,
    String? customerName,
    String? referenceId,
  }) async {
    try {
      if (!PaymentConfig.enableOrangeMoney) {
        throw PaymentException(
          message: 'Orange Money payments are not enabled',
          code: 'payment_method_disabled',
        );
      }

      // Format de données attendu par l'API Orange Money
      final data = {
        'amount': amount,
        'currency': currency,
        'description': description,
        'customer_phone': customerPhone,
        'customer_email': customerEmail,
        'customer_name': customerName,
        'reference_id': referenceId ?? _generateReferenceId(),
        'callback_url': PaymentConfig.paymentCallbackUrl,
      };

      // Appel à l'API backend qui contactera Orange Money
      final response = await _apiClient.post(
        '/subscriptions/payment/orange-money/initialize',
        data: data,
      );

      if (response['success']) {
        return response['data'];
      } else {
        throw PaymentException(
          message: response['message'] ?? 'Failed to initialize Orange Money payment',
          code: response['code'],
        );
      }
    } catch (e) {
      if (e is PaymentException) {
        rethrow;
      }
      throw PaymentException(
        message: e.toString(),
        code: 'payment_initialization_failed',
      );
    }
  }

  // Vérifier le statut d'un paiement Orange Money
  Future<Map<String, dynamic>> checkOrangeMoneyPaymentStatus(String paymentId) async {
    try {
      final response = await _apiClient.get(
        '/subscriptions/payment/orange-money/status/$paymentId',
      );

      if (response['success']) {
        return response['data'];
      } else {
        throw PaymentException(
          message: response['message'] ?? 'Failed to check payment status',
          code: response['code'],
        );
      }
    } catch (e) {
      if (e is PaymentException) {
        rethrow;
      }
      throw PaymentException(
        message: e.toString(),
        code: 'payment_status_check_failed',
      );
    }
  }

  // Initialiser un paiement par carte
  Future<Map<String, dynamic>> initializeCreditCardPayment({
    required String amount,
    required String currency,
    required String description,
    String? customerEmail,
    String? customerName,
    String? referenceId,
  }) async {
    try {
      if (!PaymentConfig.enableCardPayment) {
        throw PaymentException(
          message: 'Credit card payments are not enabled',
          code: 'payment_method_disabled',
        );
      }

      // Format de données attendu par l'API de paiement par carte
      final data = {
        'amount': amount,
        'currency': currency,
        'description': description,
        'customer_email': customerEmail,
        'customer_name': customerName,
        'reference_id': referenceId ?? _generateReferenceId(),
        'callback_url': PaymentConfig.paymentCallbackUrl,
      };

      // Appel à l'API backend
      final response = await _apiClient.post(
        '/subscriptions/payment/credit-card/initialize',
        data: data,
      );

      if (response['success']) {
        return response['data'];
      } else {
        throw PaymentException(
          message: response['message'] ?? 'Failed to initialize credit card payment',
          code: response['code'],
        );
      }
    } catch (e) {
      if (e is PaymentException) {
        rethrow;
      }
      throw PaymentException(
        message: e.toString(),
        code: 'payment_initialization_failed',
      );
    }
  }

  // Initialiser une demande de paiement manuel
  Future<Map<String, dynamic>> initializeManualPayment({
    required String amount,
    required String currency,
    required String plan,
    required int durationMonths,
    String? referenceId,
  }) async {
    try {
      // Format de données attendu par l'API backend
      final data = {
        'amount': amount,
        'currency': currency,
        'plan': plan,
        'duration_months': durationMonths,
        'reference_id': referenceId ?? _generateReferenceId(),
      };

      // Appel à l'API backend
      final response = await _apiClient.post(
        '/subscriptions/payment/manual/initialize',
        data: data,
      );

      if (response['success']) {
        return response['data'];
      } else {
        throw PaymentException(
          message: response['message'] ?? 'Failed to initialize manual payment',
          code: response['code'],
        );
      }
    } catch (e) {
      if (e is PaymentException) {
        rethrow;
      }
      throw PaymentException(
        message: e.toString(),
        code: 'payment_initialization_failed',
      );
    }
  }

  // Vérifier le statut d'un paiement
  Future<PaymentStatus> checkPaymentStatus(String paymentId, PaymentMethod method) async {
    try {
      final String endpoint;

      switch (method) {
        case PaymentMethod.orangeMoney:
          endpoint = '/subscriptions/payment/orange-money/status/$paymentId';
          break;
        case PaymentMethod.creditCard:
          endpoint = '/subscriptions/payment/credit-card/status/$paymentId';
          break;
        case PaymentMethod.manual:
          endpoint = '/subscriptions/payment/manual/status/$paymentId';
          break;
      }

      final response = await _apiClient.get(endpoint);

      if (response['success']) {
        final status = response['data']['status'];

        switch (status) {
          case 'initialized':
            return PaymentStatus.initialized;
          case 'pending':
            return PaymentStatus.pending;
          case 'processing':
            return PaymentStatus.processing;
          case 'completed':
            return PaymentStatus.completed;
          case 'failed':
            return PaymentStatus.failed;
          case 'cancelled':
            return PaymentStatus.cancelled;
          case 'refunded':
            return PaymentStatus.refunded;
          default:
            return PaymentStatus.pending;
        }
      } else {
        throw PaymentException(
          message: response['message'] ?? 'Failed to check payment status',
          code: response['code'],
        );
      }
    } catch (e) {
      if (e is PaymentException) {
        rethrow;
      }
      throw PaymentException(
        message: e.toString(),
        code: 'payment_status_check_failed',
      );
    }
  }

  // Générer un ID de référence unique
  String _generateReferenceId() {
    final now = DateTime.now();
    final timestamp = now.millisecondsSinceEpoch.toString();
    final random = timestamp.substring(timestamp.length - 6);
    return 'ST-${now.year}${now.month.toString().padLeft(2, '0')}${now.day.toString().padLeft(2, '0')}-$random';
  }

  // Calculer le prix de l'abonnement
// Calculer le prix de l'abonnement
  double calculateSubscriptionPrice(
      String plan,
      int durationMonths,
      String? promoCode,
      ) {
    if (!PaymentConfig.subscriptionPlans.containsKey(plan)) {
      throw PaymentException(
        message: 'Invalid subscription plan: $plan',
        code: 'invalid_plan',
      );
    }

    final planDetails = PaymentConfig.subscriptionPlans[plan]!;
    double basePrice;

    // Déterminer le prix de base selon la durée
    if (durationMonths >= 12) {
      // Prix annuel
      basePrice = planDetails['yearly_price'];
    } else if (durationMonths >= 3) {
      // Prix trimestriel
      basePrice = planDetails['quarterly_price'];
    } else {
      // Prix mensuel
      basePrice = planDetails['monthly_price'] * durationMonths;
    }

    // Appliquer le code promo si fourni et valide
    if (promoCode != null && PaymentConfig.promoDiscounts.containsKey(promoCode)) {
      final discount = PaymentConfig.promoDiscounts[promoCode]!;
      basePrice = basePrice * (1 - discount);
    }

    return double.parse(basePrice.toStringAsFixed(2));
  }

  // Obtenir l'historique des paiements
  Future<List<Map<String, dynamic>>> getPaymentHistory() async {
    try {
      final response = await _apiClient.get('/subscriptions/transactions');

      if (response['success']) {
        return List<Map<String, dynamic>>.from(response['data']);
      } else {
        throw PaymentException(
          message: response['message'] ?? 'Failed to retrieve payment history',
          code: response['code'],
        );
      }
    } catch (e) {
      if (e is PaymentException) {
        rethrow;
      }
      throw PaymentException(
        message: e.toString(),
        code: 'payment_history_failed',
      );
    }
  }

  // Vérifier la validité d'un code promo
  Future<Map<String, dynamic>> validatePromoCode(String code, String plan) async {
    try {
      final response = await _apiClient.post(
        '/subscriptions/check-promo',
        data: {
          'code': code,
          'plan': plan,
        },
      );

      if (response['success']) {
        return response['data'];
      } else {
        throw PaymentException(
          message: response['message'] ?? 'Invalid promotion code',
          code: response['code'] ?? 'invalid_promo_code',
        );
      }
    } catch (e) {
      if (e is PaymentException) {
        rethrow;
      }
      throw PaymentException(
        message: e.toString(),
        code: 'promo_validation_failed',
      );
    }
  }
}