// lib/modules/splash_screen.dart
import 'package:flutter/material.dart';
import 'package:auto_route/auto_route.dart';
import 'package:smart_turf/routes/app_router.dart';
import 'package:provider/provider.dart';
import 'package:smart_turf/data/providers/auth_provider.dart';
import 'dart:async';

@RoutePage()
class SplashScreen extends StatefulWidget {
  const SplashScreen({Key? key}) : super(key: key);

  @override
  _SplashScreenState createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _checkAuthStatus();
  }

  Future<void> _checkAuthStatus() async {
    // Délai d'affichage du splash screen
    await Future.delayed(const Duration(seconds: 2));

    if (!mounted) return;

    final authProvider = Provider.of<AuthProvider>(context, listen: false);

    // Vérifier si l'utilisateur a déjà vu l'onboarding
    final isOnboardingCompleted = true; // À remplacer par la vérification réelle

    if (isOnboardingCompleted) {
      // Vérifier l'état d'authentification
      if (authProvider.isAuthenticated) {
        context.router.replace(const HomeRoute());
      } else {
        context.router.replace(const LoginRoute());
      }
    } else {
      context.router.replace(const OnboardingRoute());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Image.asset(
              'assets/images/logo.png',
              height: 120,
              errorBuilder: (context, error, stackTrace) =>
              const Icon(Icons.sports_score, size: 120),
            ),
            const SizedBox(height: 24),
            const CircularProgressIndicator(),
          ],
        ),
      ),
    );
  }
}