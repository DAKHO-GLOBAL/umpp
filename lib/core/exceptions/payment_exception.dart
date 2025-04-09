class PaymentException implements Exception {
  final String message;
  final String? code;
  final Map<String, dynamic>? data;

  PaymentException({
    required this.message,
    this.code,
    this.data,
  });

  factory PaymentException.connectionError() {
    return PaymentException(
      message: 'Problème de connexion au service de paiement. Veuillez vérifier votre connexion internet.',
      code: 'payment_connection_error',
    );
  }

  factory PaymentException.timeout() {
    return PaymentException(
      message: 'La transaction a expiré. Veuillez réessayer.',
      code: 'payment_timeout',
    );
  }

  factory PaymentException.invalidPaymentMethod() {
    return PaymentException(
      message: 'Méthode de paiement non valide ou non prise en charge.',
      code: 'invalid_payment_method',
    );
  }

  factory PaymentException.insufficientFunds() {
    return PaymentException(
      message: 'Fonds insuffisants pour effectuer ce paiement.',
      code: 'insufficient_funds',
    );
  }

  factory PaymentException.paymentDeclined() {
    return PaymentException(
      message: 'Paiement refusé par l\'émetteur de la carte ou le service de paiement.',
      code: 'payment_declined',
    );
  }

  factory PaymentException.invalidAmount() {
    return PaymentException(
      message: 'Montant de paiement non valide.',
      code: 'invalid_amount',
    );
  }

  factory PaymentException.paymentCancelled() {
    return PaymentException(
      message: 'Paiement annulé par l\'utilisateur.',
      code: 'payment_cancelled',
    );
  }

  factory PaymentException.transactionFailed() {
    return PaymentException(
      message: 'La transaction a échoué. Veuillez réessayer ultérieurement.',
      code: 'transaction_failed',
    );
  }

  @override
  String toString() {
    return 'PaymentException: $message (Code: $code)';
  }
}