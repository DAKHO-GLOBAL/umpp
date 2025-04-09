import 'package:auto_route/auto_route.dart';
import 'package:smart_turf/data/providers/auth_provider.dart';
import 'package:provider/provider.dart';

class AuthGuard extends AutoRouteGuard {
  @override
  void onNavigation(NavigationResolver resolver, StackRouter router) {
    // Vérifier l'état d'authentification de l'utilisateur
    final authProvider = resolver.context.read<AuthProvider>();

    if (authProvider.isAuthenticated) {
      // L'utilisateur est authentifié, continuer la navigation
      resolver.next(true);
    } else {
      // L'utilisateur n'est pas authentifié, rediriger vers la page de connexion
      router.push(const LoginRoute());
    }
  }
}

class VerificationGuard extends AutoRouteGuard {
  @override
  void onNavigation(NavigationResolver resolver, StackRouter router) {
    // Vérifier si l'email de l'utilisateur est vérifié
    final authProvider = resolver.context.read<AuthProvider>();

    if (authProvider.isAuthenticated) {
      if (authProvider.isEmailVerified) {
        // L'email est vérifié, continuer la navigation
        resolver.next(true);
      } else {
        // L'email n'est pas vérifié, rediriger vers la page de vérification
        router.push(const VerifyEmailRoute());
      }
    } else {
      // L'utilisateur n'est pas authentifié, rediriger vers la page de connexion
      router.push(const LoginRoute());
    }
  }
}

class SubscriptionGuard extends AutoRouteGuard {
  final String requiredLevel;

  SubscriptionGuard(this.requiredLevel);

  @override
  void onNavigation(NavigationResolver resolver, StackRouter router) {
    // Vérifier le niveau d'abonnement de l'utilisateur
    final authProvider = resolver.context.read<AuthProvider>();

    if (authProvider.isAuthenticated) {
      final user = authProvider.currentUser;

      if (user != null) {
        if (_hasRequiredSubscription(user.subscriptionLevel)) {
          // L'utilisateur a l'abonnement requis, continuer la navigation
          resolver.next(true);
        } else {
          // L'utilisateur n'a pas l'abonnement requis, rediriger vers la page d'abonnement
          router.push(const SubscriptionsRoute());
        }
      } else {
        // Impossible de déterminer l'abonnement, rediriger vers la page de connexion
        router.push(const LoginRoute());
      }
    } else {
      // L'utilisateur n'est pas authentifié, rediriger vers la page de connexion
      router.push(const LoginRoute());
    }
  }

  // Vérifier si le niveau d'abonnement est suffisant
  bool _hasRequiredSubscription(String userLevel) {
    // Hiérarchie des niveaux d'abonnement
    final levels = {
      'free': 0,
      'standard': 1,
      'premium': 2,
    };

    final userLevelValue = levels[userLevel] ?? 0;
    final requiredLevelValue = levels[requiredLevel] ?? 0;

    return userLevelValue >= requiredLevelValue;
  }
}