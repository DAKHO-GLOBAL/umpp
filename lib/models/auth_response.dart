import 'package:smart_turf/models/user.dart';

class AuthResponse {
  final bool success;
  final String message;
  final String? accessToken;
  final String? refreshToken;
  final User? user;

  AuthResponse({
    required this.success,
    required this.message,
    this.accessToken,
    this.refreshToken,
    this.user,
  });

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    return AuthResponse(
      success: json['success'] ?? false,
      message: json['message'] ?? '',
      accessToken: json['access_token'],
      refreshToken: json['refresh_token'],
      user: json['user'] != null ? User.fromJson(json['user']) : null,
    );
  }

  factory AuthResponse.error(String errorMessage) {
    return AuthResponse(
      success: false,
      message: errorMessage,
    );
  }
}