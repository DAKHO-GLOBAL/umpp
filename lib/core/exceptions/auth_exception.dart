class AuthException implements Exception {
  final String message;
  final String? code;

  AuthException({
    required this.message,
    this.code,
  });

  factory AuthException.invalidEmail() {
    return AuthException(
      message: 'L\'adresse email est invalide.',
      code: 'invalid-email',
    );
  }

  factory AuthException.userDisabled() {
    return AuthException(
      message: 'Ce compte a été désactivé.',
      code: 'user-disabled',
    );
  }

  factory AuthException.userNotFound() {
    return AuthException(
      message: 'Aucun compte n\'existe avec cet email.',
      code: 'user-not-found',
    );
  }

  factory AuthException.wrongPassword() {
    return AuthException(
      message: 'Mot de passe incorrect.',
      code: 'wrong-password',
    );
  }

  factory AuthException.emailAlreadyInUse() {
    return AuthException(
      message: 'Cette adresse email est déjà utilisée par un autre compte.',
      code: 'email-already-in-use',
    );
  }

  factory AuthException.weakPassword() {
    return AuthException(
      message: 'Le mot de passe est trop faible.',
      code: 'weak-password',
    );
  }

  factory AuthException.operationNotAllowed() {
    return AuthException(
      message: 'Cette opération n\'est pas autorisée.',
      code: 'operation-not-allowed',
    );
  }

  factory AuthException.expiredActionCode() {
    return AuthException(
      message: 'Le code d\'action a expiré.',
      code: 'expired-action-code',
    );
  }

  factory AuthException.invalidActionCode() {
    return AuthException(
      message: 'Le code d\'action est invalide.',
      code: 'invalid-action-code',
    );
  }

  factory AuthException.tooManyRequests() {
    return AuthException(
      message: 'Trop de tentatives. Veuillez réessayer plus tard.',
      code: 'too-many-requests',
    );
  }

  factory AuthException.sessionExpired() {
    return AuthException(
      message: 'Votre session a expiré. Veuillez vous reconnecter.',
      code: 'session-expired',
    );
  }

  factory AuthException.requiresRecentLogin() {
    return AuthException(
      message: 'Cette opération nécessite une connexion récente. Veuillez vous reconnecter.',
      code: 'requires-recent-login',
    );
  }

  @override
  String toString() {
    return 'AuthException: $message (Code: $code)';
  }
}