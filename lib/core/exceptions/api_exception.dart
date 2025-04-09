class ApiException implements Exception {
  final String message;
  final String? code;
  final int? statusCode;
  final Map<String, dynamic>? data;

  ApiException({
    required this.message,
    this.code,
    this.statusCode,
    this.data,
  });

  factory ApiException.fromJson(Map<String, dynamic> json) {
    return ApiException(
      message: json['message'] ?? 'Une erreur est survenue',
      code: json['code'],
      statusCode: json['status_code'],
      data: json['data'],
    );
  }

  factory ApiException.networkError() {
    return ApiException(
      message: 'Problème de connexion réseau. Veuillez vérifier votre connexion internet.',
      code: 'network_error',
    );
  }

  factory ApiException.serverError() {
    return ApiException(
      message: 'Erreur serveur. Veuillez réessayer plus tard.',
      code: 'server_error',
      statusCode: 500,
    );
  }

  factory ApiException.timeout() {
    return ApiException(
      message: 'La requête a pris trop de temps. Veuillez réessayer.',
      code: 'timeout',
    );
  }

  factory ApiException.unauthorized() {
    return ApiException(
      message: 'Session expirée. Veuillez vous reconnecter.',
      code: 'unauthorized',
      statusCode: 401,
    );
  }

  factory ApiException.forbidden() {
    return ApiException(
      message: 'Vous n\'avez pas l\'autorisation d\'effectuer cette action.',
      code: 'forbidden',
      statusCode: 403,
    );
  }

  factory ApiException.notFound() {
    return ApiException(
      message: 'La ressource demandée n\'existe pas.',
      code: 'not_found',
      statusCode: 404,
    );
  }

  @override
  String toString() {
    return 'ApiException: $message (Code: $code, Status: $statusCode)';
  }
}