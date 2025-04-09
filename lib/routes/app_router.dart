import 'package:auto_route/auto_route.dart';
import 'package:flutter/material.dart';
import 'package:smart_turf/modules/auth/login_screen.dart';
import 'package:smart_turf/modules/auth/register_screen.dart';
import 'package:smart_turf/modules/auth/password_reset_screen.dart';
import 'package:smart_turf/modules/auth/verify_email_screen.dart';
import 'package:smart_turf/modules/auth/verify_phone_screen.dart';
import 'package:smart_turf/routes/route_guards.dart';

part 'app_router.gr.dart';

@AutoRouterConfig()
class AppRouter extends _$AppRouter {
  @override
  List<AutoRoute> get routes => [
    // Routes d'authentification
    AutoRoute(
      path: '/',
      page: SplashRoute.page,
      initial: true,
    ),
    AutoRoute(
      path: '/onboarding',
      page: OnboardingRoute.page,
    ),
    AutoRoute(
      path: '/login',
      page: LoginRoute.page,
    ),
    AutoRoute(
      path: '/register',
      page: RegisterRoute.page,
    ),
    AutoRoute(
      path: '/forgot-password',
      page: PasswordResetRoute.page,
    ),
    AutoRoute(
      path: '/verify-email',
      page: VerifyEmailRoute.page,
    ),
    AutoRoute(
      path: '/verify-phone',
      page: VerifyPhoneRoute.page,
    ),

    // Routes principales, protégées par l'authentification
    AutoRoute(
      path: '/home',
      page: HomeRoute.page,
      guards: [AuthGuard()],
      children: [
        AutoRoute(
          path: 'dashboard',
          page: DashboardRoute.page,
        ),
        AutoRoute(
          path: 'courses',
          page: CoursesRoute.page,
        ),
        AutoRoute(
          path: 'predictions',
          page: PredictionsRoute.page,
        ),
        AutoRoute(
          path: 'profile',
          page: ProfileRoute.page,
        ),
      ],
    ),

    // Routes détaillées pour les courses et prédictions
    AutoRoute(
      path: '/courses/:id',
      page: CourseDetailRoute.page,
      guards: [AuthGuard()],
    ),
    AutoRoute(
      path: '/predictions/:id',
      page: PredictionDetailRoute.page,
      guards: [AuthGuard()],
    ),

    // Routes d'abonnement et de paiement
    AutoRoute(
      path: '/subscriptions',
      page: SubscriptionsRoute.page,
      guards: [AuthGuard()],
    ),
    AutoRoute(
      path: '/payment/:plan',
      page: PaymentRoute.page,
      guards: [AuthGuard()],
    ),
    AutoRoute(
      path: '/payment-confirmation',
      page: PaymentConfirmationRoute.page,
      guards: [AuthGuard()],
    ),
  ];
}

// Définition des routes
@RoutePage()
class SplashScreen extends StatelessWidget {
  const SplashScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Text('Splash Screen'),
      ),
    );
  }
}

@RoutePage()
class OnboardingScreen extends StatelessWidget {
  const OnboardingScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Text('Onboarding Screen'),
      ),
    );
  }
}

@RoutePage()
class HomeScreen extends StatelessWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Text('Home Screen'),
      ),
    );
  }
}

@RoutePage()
class DashboardScreen extends StatelessWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Text('Dashboard Screen'),
      ),
    );
  }
}

@RoutePage()
class CoursesScreen extends StatelessWidget {
  const CoursesScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Text('Courses Screen'),
      ),
    );
  }
}

@RoutePage()
class CourseDetailScreen extends StatelessWidget {
  final int id;

  const CourseDetailScreen({Key? key, @PathParam('id') required this.id}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Text('Course Detail Screen: $id'),
      ),
    );
  }
}

@RoutePage()
class PredictionsScreen extends StatelessWidget {
  const PredictionsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Text('Predictions Screen'),
      ),
    );
  }
}

@RoutePage()
class PredictionDetailScreen extends StatelessWidget {
  final int id;

  const PredictionDetailScreen({Key? key, @PathParam('id') required this.id}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Text('Prediction Detail Screen: $id'),
      ),
    );
  }
}

@RoutePage()
class ProfileScreen extends StatelessWidget {
  const ProfileScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Text('Profile Screen'),
      ),
    );
  }
}

@RoutePage()
class SubscriptionsScreen extends StatelessWidget {
  const SubscriptionsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Text('Subscriptions Screen'),
      ),
    );
  }
}

@RoutePage()
class PaymentScreen extends StatelessWidget {
  final String plan;

  const PaymentScreen({Key? key, @PathParam('plan') required this.plan}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Text('Payment Screen for plan: $plan'),
      ),
    );
  }
}

@RoutePage()
class PaymentConfirmationScreen extends StatelessWidget {
  const PaymentConfirmationScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Text('Payment Confirmation Screen'),
      ),
    );
  }
}