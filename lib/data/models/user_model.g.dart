// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'user_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

UserModel _$UserModelFromJson(Map<String, dynamic> json) => UserModel(
      id: (json['id'] as num).toInt(),
      email: json['email'] as String,
      username: json['username'] as String,
      firstName: json['firstName'] as String?,
      lastName: json['lastName'] as String?,
      profilePicture: json['profilePicture'] as String?,
      bio: json['bio'] as String?,
      isActive: json['isActive'] as bool,
      isAdmin: json['isAdmin'] as bool,
      isVerified: json['isVerified'] as bool,
      subscriptionLevel: json['subscriptionLevel'] as String,
      subscriptionStart: json['subscriptionStart'] == null
          ? null
          : DateTime.parse(json['subscriptionStart'] as String),
      subscriptionExpiry: json['subscriptionExpiry'] == null
          ? null
          : DateTime.parse(json['subscriptionExpiry'] as String),
      billingAddress: json['billingAddress'] as String?,
      createdAt: json['created_at'] == null
          ? null
          : DateTime.parse(json['created_at'] as String),
      lastLogin: json['last_login'] == null
          ? null
          : DateTime.parse(json['last_login'] as String),
    );

Map<String, dynamic> _$UserModelToJson(UserModel instance) => <String, dynamic>{
      'id': instance.id,
      'email': instance.email,
      'username': instance.username,
      'firstName': instance.firstName,
      'lastName': instance.lastName,
      'profilePicture': instance.profilePicture,
      'bio': instance.bio,
      'isActive': instance.isActive,
      'isAdmin': instance.isAdmin,
      'isVerified': instance.isVerified,
      'subscriptionLevel': instance.subscriptionLevel,
      'subscriptionStart': instance.subscriptionStart?.toIso8601String(),
      'subscriptionExpiry': instance.subscriptionExpiry?.toIso8601String(),
      'billingAddress': instance.billingAddress,
      'created_at': instance.createdAt?.toIso8601String(),
      'last_login': instance.lastLogin?.toIso8601String(),
    };
