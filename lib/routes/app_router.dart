// lib/routes/app_router.dart
import 'package:auto_route/auto_route.dart';
import 'package:flutter/material.dart';
import 'package:smart_turf/modules/auth/login_screen.dart';
import 'package:smart_turf/modules/auth/register_screen.dart';
import 'package:smart_turf/modules/auth/password_reset_screen.dart';
import 'package:smart_turf/modules/auth/verify_email_screen.dart';
import 'package:smart_turf/modules/auth/verify_phone_screen.dart';
import 'package:smart_turf/modules/auth/auth_wrapper.dart';
import 'package:smart_turf/modules/home/home_screen.dart';
import 'package:smart_turf/modules/home/dashboard_screen.dart';
import 'package:smart_turf/modules/courses/courses_screen.dart';
import 'package:smart_turf/modules/courses/course_detail_screen.dart';
import 'package:smart_turf/modules/predictions/predictions_screen.dart';
import 'package:smart_turf/modules/predictions/prediction_detail_screen.dart';
import 'package:smart_turf/modules/profile/profile_screen.dart';
import 'package:smart_turf/modules/subscription/subscriptions_screen.dart';
import 'package:smart_turf/modules/subscription/payment_screen.dart';
import 'package:smart_turf/modules/subscription/payment_confirmation_screen.dart';
import 'package:smart_turf/routes/route_guards.dart';
import 'package:smart_turf/modules/splash_screen.dart';
import 'package:smart_turf/modules/onboarding/onboarding_screen.dart';

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
      path: '/auth-wrapper',
      page: AuthWrapper.page,
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