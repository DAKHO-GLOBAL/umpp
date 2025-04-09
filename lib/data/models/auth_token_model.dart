import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'auth_token_model.g.dart';

@JsonSerializable()
class AuthTokenModel extends Equatable {
  @JsonKey(name: 'access_token')
  final String accessToken;

  @JsonKey(name: 'refresh_token')
  final String refreshToken;

  @JsonKey(name: 'expires_in')
  final int expiresIn;

  @JsonKey(name: 'token_type')
  final String tokenType;

  @JsonKey(name: 'user_id')
  final String? userId;

  const AuthTokenModel({
    required this.accessToken,
    required this.refreshToken,
    required this.expiresIn,
    required this.tokenType,
    this.userId,
  });

  // Factory pour créer une instance à partir de JSON
  factory AuthTokenModel.fromJson(Map<String, dynamic> json) {
    // Gérer la réponse de l'API qui peut avoir des structures différentes
    if (json.containsKey('data')) {
      return _$AuthTokenModelFromJson(json['data'] as Map<String, dynamic>);
    }
    return _$AuthTokenModelFromJson(json);
  }

  // Convertir en JSON
  Map<String, dynamic> toJson() => _$AuthTokenModelToJson(this);

  // Calculer la date d'expiration
  DateTime get expirationDate {
    final now = DateTime.now();
    return now.add(Duration(seconds: expiresIn));
  }

  // Vérifier si le token est expiré
  bool get isExpired {
    final now = DateTime.now();
    return now.isAfter(expirationDate);
  }

  // Utilisé par Equatable pour comparer des objets
  @override
  List<Object?> get props => [accessToken, refreshToken, expiresIn, tokenType, userId];
}