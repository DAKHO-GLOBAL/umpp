import 'package:smart_turf/config/payment_config.dart';
import 'package:smart_turf/core/exceptions/payment_exception.dart';
import 'package:smart_turf/services/api/api_client.dart';
import 'package:smart_turf/services/payment/payment_service.dart';

class SubscriptionService {
  static final SubscriptionService _instance = SubscriptionService._internal();
  final ApiClient _apiClient;
  final PaymentService _paymentService;

  factory SubscriptionService(ApiClient apiClient, PaymentService paymentService) {
    _instance._apiClient = apiClient;
    _instance._paymentService = paymentService;
    return _instance;
  }

  SubscriptionService._internal()
      : _apiClient = ApiClient(null),
        _paymentService = PaymentService(ApiClient(null));

  // Obtenir la liste des plans d'abonnement
  Future<List<Map<String, dynamic>>> getSubscriptionPlans() async {
    try {
      final response = await _apiClient.get('/subscriptions/plans');

      if (response['success']) {
        return List<Map<String, dynamic>>.from(response['data']);
      } else {
        throw PaymentException(
          message: response['message'] ?? 'Failed to retrieve subscription plans',
          code: response['code'],
        );
      }
    } catch (e) {
      if (e is PaymentException) {
        rethrow;
      }
      throw PaymentException(
        message: e.toString(),
        code: 'subscription_plans_failed',
      );
    }
  }

  // S'abonner à un plan
  Future<Map<String, dynamic>> subscribe({
    required String plan,
    required int durationMonths,
    required PaymentMethod paymentMethod,
    String? promoCode,
    String? customerPhone,
    String? customerEmail,
    String? customerName,
  }) async {
    try {
      // Calculer le prix de l'abonnement
      final double price = _paymentService.calculateSubscriptionPrice(
        plan,
        durationMonths,
        promoCode,
      );

      // Initialiser le paiement selon la méthode choisie
      Map<String, dynamic> paymentInitResponse;

      switch (paymentMethod) {
        case PaymentMethod.orangeMoney:
          if (customerPhone == null) {
            throw PaymentException(
              message: 'Phone number is required for Orange Money payments',
              code: 'missing_phone_number',
            );
          }

          paymentInitResponse = await _paymentService.initializeOrangeMoneyPayment(
            amount: price.toString(),
            currency: 'XOF',
            description: 'Abonnement $plan pour $durationMonths mois',
            customerPhone: customerPhone,
            customerEmail: customerEmail,
            customerName: customerName,
          );
          break;

        case PaymentMethod.creditCard:
          paymentInitResponse = await _paymentService.initializeCreditCardPayment(
            amount: price.toString(),
            currency: 'XOF',
            description: 'Abonnement $plan pour $durationMonths mois',
            customerEmail: customerEmail,
            customerName: customerName,
          );
          break;

        case PaymentMethod.manual:
          paymentInitResponse = await _paymentService.initializeManualPayment(
            amount: price.toString(),
            currency: 'XOF',
            plan: plan,
            durationMonths: durationMonths,
          );
          break;
      }

      // Créer l'abonnement
      final subscribeResponse = await _apiClient.post(
        '/subscriptions/subscribe',
        data: {
          'plan': plan,
          'duration_months': durationMonths,
          'payment_method': paymentMethod.toString().split('.').last,
          'promotion_code': promoCode,
          'payment_reference': paymentInitResponse['payment_id'],
          'price': price,
        },
      );

      if (subscribeResponse['success']) {
        return {
          ...subscribeResponse['data'],
          ...paymentInitResponse,
        };
      } else {
        throw PaymentException(
          message: subscribeResponse['message'] ?? 'Failed to create subscription',
          code: subscribeResponse['code'],
        );
      }
    } catch (e) {
      if (e is PaymentException) {
        rethrow;
      }
      throw PaymentException(
        message: e.toString(),
        code: 'subscription_failed',
      );
    }
  }

  // Annuler un abonnement
  Future<bool> cancelSubscription({bool immediate = false}) async {
    try {
      final response = await _apiClient.post(
        '/subscriptions/cancel',
        data: {
          'immediate': immediate,
        },
      );

      return response['success'] ?? false;
    } catch (e) {
      if (e is PaymentException) {
        rethrow;
      }
      throw PaymentException(
        message: e.toString(),
        code: 'cancel_subscription_failed',
      );
    }
  }

  // Changer de plan d'abonnement
  Future<Map<String, dynamic>> changeSubscriptionPlan({
    required String newPlan,
    required PaymentMethod paymentMethod,
    String? promoCode,
  }) async {
    try {
      final response = await _apiClient.post(
        '/subscriptions/change',
        data: {
          'plan': newPlan,
          'payment_method': paymentMethod.toString().split('.').last,
          'promotion_code': promoCode,
        },
      );

      if (response['success']) {
        return response['data'];
      } else {
        throw PaymentException(
          message: response['message'] ?? 'Failed to change subscription plan',
          code: response['code'],
        );
      }
    } catch (e) {
      if (e is PaymentException) {
        rethrow;
      }
      throw PaymentException(
        message: e.toString(),
        code: 'change_plan_failed',
      );
    }
  }

  // Obtenir les détails de l'abonnement actuel
  Future<Map<String, dynamic>> getCurrentSubscription() async {
    try {
      final response = await _apiClient.get('/subscriptions/current');

      if (response['success']) {
        return response['data'];
      } else {
        throw PaymentException(
          message: response['message'] ?? 'Failed to retrieve current subscription',
          code: response['code'],
        );
      }
    } catch (e) {
      if (e is PaymentException) {
        rethrow;
      }
      throw PaymentException(
        message: e.toString(),
        code: 'get_subscription_failed',
      );
    }
  }

  // Obtenir les quotas d'utilisation
  Future<Map<String, dynamic>> getUsageQuotas() async {
    try {
      final response = await _apiClient.get('/subscriptions/usage');

      if (response['success']) {
        return response['data'];
      } else {
        throw PaymentException(
          message: response['message'] ?? 'Failed to retrieve usage quotas',
          code: response['code'],
        );
      }
    } catch (e) {
      if (e is PaymentException) {
        rethrow;
      }
      throw PaymentException(
        message: e.toString(),
        code: 'get_quotas_failed',
      );
    }
  }
}