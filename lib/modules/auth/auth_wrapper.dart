import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:auto_route/auto_route.dart';
import 'package:smart_turf/core/widgets/loading_indicator.dart';
import 'package:smart_turf/data/providers/auth_provider.dart';
import 'package:smart_turf/routes/app_router.dart';

@RoutePage()
class AuthWrapper extends StatelessWidget {
  const AuthWrapper({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);

    // Selon l'état d'authentification, rediriger l'utilisateur
    switch (authProvider.status) {
      case AuthStatus.initial:
      case AuthStatus.authenticating:
        return LoadingIndicator(
          withScaffold: true,
          message: 'Vérification de la session...',
        );

      case AuthStatus.authenticated:
      // Vérifier si l'email de l'utilisateur est vérifié
        if (!authProvider.isEmailVerified) {
          // Rediriger vers la page de vérification d'email
          context.router.replace(const VerifyEmailRoute());
          return Container(); // Placeholder pendant la navigation
        }
        // Rediriger vers la page d'accueil
        context.router.replace(const HomeRoute());
        return Container(); // Placeholder pendant la navigation

      case AuthStatus.unauthenticated:
      // Rediriger vers la page d'accueil ou de login selon les préférences
        context.router.replace(const LoginRoute());
        return Container(); // Placeholder pendant la navigation

      case AuthStatus.error:
      // Montrer une erreur et rediriger vers la connexion
        return Scaffold(
          body: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline, color: Colors.red, size: 48),
                const SizedBox(height: 16),
                Text(
                  'Impossible de vérifier votre identité',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                Text(
                  authProvider.errorMessage ?? 'Veuillez vous reconnecter',
                  style: Theme.of(context).textTheme.bodyMedium,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: () {
                    authProvider.clearError();
                    context.router.replace(const LoginRoute());
                  },
                  child: const Text('Se connecter'),
                ),
              ],
            ),
          ),
        );
    }
  }
}