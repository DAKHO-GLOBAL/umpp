class User {
  final int id;
  final String email;
  final String username;
  final String? firstName;
  final String? lastName;
  final String subscriptionLevel;
  final bool isActive;
  final bool isAdmin;
  final bool isVerified;
  final String? profilePicture;
  final DateTime? subscriptionExpiry;

  User({
    required this.id,
    required this.email,
    required this.username,
    this.firstName,
    this.lastName,
    required this.subscriptionLevel,
    required this.isActive,
    required this.isAdmin,
    required this.isVerified,
    this.profilePicture,
    this.subscriptionExpiry,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] ?? 0,
      email: json['email'] ?? '',
      username: json['username'] ?? '',
      firstName: json['first_name'],
      lastName: json['last_name'],
      subscriptionLevel: json['subscription_level'] ?? 'free',
      isActive: json['is_active'] ?? true,
      isAdmin: json['is_admin'] ?? false,
      isVerified: json['is_verified'] ?? false,
      profilePicture: json['profile_picture'],
      subscriptionExpiry: json['subscription'] != null && json['subscription']['expiry'] != null
          ? DateTime.parse(json['subscription']['expiry'])
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'username': username,
      'first_name': firstName,
      'last_name': lastName,
      'subscription_level': subscriptionLevel,
      'is_active': isActive,
      'is_admin': isAdmin,
      'is_verified': isVerified,
      'profile_picture': profilePicture,
      'subscription': {
        'expiry': subscriptionExpiry?.toIso8601String()
      }
    };
  }

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
}