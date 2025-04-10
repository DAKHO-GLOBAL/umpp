class ApiResponse<T> {
  final bool success;
  final String message;
  final T? data;
  final Map<String, dynamic>? errors;

  ApiResponse({
    required this.success,
    required this.message,
    this.data,
    this.errors,
  });

  factory ApiResponse.fromJson(Map<String, dynamic> json, T Function(dynamic) fromJsonT) {
    return ApiResponse(
      success: json['success'] ?? false,
      message: json['message'] ?? '',
      data: json['data'] != null ? fromJsonT(json['data']) : null,
      errors: json['errors'] as Map<String, dynamic>?,
    );
  }

  factory ApiResponse.error(String errorMessage) {
    return ApiResponse(
      success: false,
      message: errorMessage,
    );
  }

  factory ApiResponse.networkError() {
    return ApiResponse(
      success: false,
      message: 'Erreur de connexion au serveur. Veuillez vérifier votre connexion internet.',
    );
  }
}