import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'user_model.g.dart';

@JsonSerializable()
class UserModel extends Equatable {
  final int id;
  final String email;
  final String username;
  final String? firstName;
  final String? lastName;
  final String? profilePicture;
  final String? bio;

  final bool isActive;
  final bool isAdmin;
  final bool isVerified;

  final String subscriptionLevel;
  final DateTime? subscriptionStart;
  final DateTime? subscriptionExpiry;

  final String? billingAddress;

  @JsonKey(name: 'created_at')
  final DateTime? createdAt;

  @JsonKey(name: 'last_login')
  final DateTime? lastLogin;

  const UserModel({
    required this.id,
    required this.email,
    required this.username,
    this.firstName,
    this.lastName,
    this.profilePicture,
    this.bio,
    required this.isActive,
    required this.isAdmin,
    required this.isVerified,
    required this.subscriptionLevel,
    this.subscriptionStart,
    this.subscriptionExpiry,
    this.billingAddress,
    this.createdAt,
    this.lastLogin,
  });

  // Obtenir le nom complet de l'utilisateur
  String get fullName {
    if (firstName != null && lastName != null) {
      return '$firstName $lastName';
    } else if (firstName != null) {
      return firstName!;
    } else if (lastName != null) {
      return lastName!;
    } else {
      return username;
    }
  }

  // Vérifier si l'abonnement est actif
  bool get isSubscriptionActive {
    if (subscriptionLevel == 'free') {
      return true;
    }

    if (subscriptionExpiry == null) {
      return false;
    }

    return DateTime.now().isBefore(subscriptionExpiry!);
  }

  // Factory pour créer une instance à partir de JSON
  factory UserModel.fromJson(Map<String, dynamic> json) => _$UserModelFromJson(json);

  // Convertir en JSON
  Map<String, dynamic> toJson() => _$UserModelToJson(this);

  // Copier l'utilisateur avec de nouvelles valeurs
  UserModel copyWith({
    int? id,
    String? email,
    String? username,
    String? firstName,
    String? lastName,
    String? profilePicture,
    String? bio,
    bool? isActive,
    bool? isAdmin,
    bool? isVerified,
    String? subscriptionLevel,
    DateTime? subscriptionStart,
    DateTime? subscriptionExpiry,
    String? billingAddress,
    DateTime? createdAt,
    DateTime? lastLogin,
  }) {
    return UserModel(
      id: id ?? this.id,
      email: email ?? this.email,
      username: username ?? this.username,
      firstName: firstName ?? this.firstName,
      lastName: lastName ?? this.lastName,
      profilePicture: profilePicture ?? this.profilePicture,
      bio: bio ?? this.bio,
      isActive: isActive ?? this.isActive,
      isAdmin: isAdmin ?? this.isAdmin,
      isVerified: isVerified ?? this.isVerified,
      subscriptionLevel: subscriptionLevel ?? this.subscriptionLevel,
      subscriptionStart: subscriptionStart ?? this.subscriptionStart,
      subscriptionExpiry: subscriptionExpiry ?? this.subscriptionExpiry,
      billingAddress: billingAddress ?? this.billingAddress,
      createdAt: createdAt ?? this.createdAt,
      lastLogin: lastLogin ?? this.lastLogin,
    );
  }

  // Utilisé par Equatable pour comparer des objets
  @override
  List<Object?> get props => [
    id, email, username, firstName, lastName, profilePicture, bio,
    isActive, isAdmin, isVerified, subscriptionLevel,
    subscriptionStart, subscriptionExpiry, billingAddress,
    createdAt, lastLogin,
  ];
}