import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_analytics/firebase_analytics.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'package:flutter/foundation.dart';
import 'package:smart_turf/config/firebase_config.dart';

class FirebaseService {
  static final FirebaseService _instance = FirebaseService._internal();

  factory FirebaseService() {
    return _instance;
  }

  FirebaseService._internal();

  late FirebaseAnalytics analytics;

  Future<void> initialize() async {
    // Configuration de Firebase Analytics
    analytics = FirebaseAnalytics.instance;
    if (FirebaseConfig.enableAnalytics) {
      await analytics.setAnalyticsCollectionEnabled(true);
      await analytics.setSessionTimeoutDuration(
        Duration(minutes: FirebaseConfig.sessionTimeout),
      );
    } else {
      await analytics.setAnalyticsCollectionEnabled(false);
    }

    // Configuration de Firebase Crashlytics
    if (FirebaseConfig.enableCrashlytics && !kDebugMode) {
      await FirebaseCrashlytics.instance.setCrashlyticsCollectionEnabled(true);
      FlutterError.onError = FirebaseCrashlytics.instance.recordFlutterError;
    } else {
      await FirebaseCrashlytics.instance.setCrashlyticsCollectionEnabled(false);
    }
  }

  // Loguer un événement Firebase Analytics
  Future<void> logEvent({
    required String name,
    Map<String, dynamic>? parameters,
  }) async {
    if (FirebaseConfig.enableAnalytics) {
      await analytics.logEvent(
        name: name,
        parameters: parameters,
      );
    }
  }

  // Définir l'utilisateur courant pour Analytics
  Future<void> setUserId(String? userId) async {
    if (FirebaseConfig.enableAnalytics) {
      await analytics.setUserId(id: userId);
    }

    // Définir l'identifiant utilisateur pour Crashlytics
    if (FirebaseConfig.enableCrashlytics &&
        FirebaseConfig.collectUserIdentifiers &&
        userId != null) {
      await FirebaseCrashlytics.instance.setUserIdentifier(userId);
    }
  }

  // Définir les propriétés utilisateur pour Analytics
  Future<void> setUserProperties({
    String? userId,
    String? userRole,
    String? subscriptionLevel,
  }) async {
    if (FirebaseConfig.enableAnalytics) {
      if (userId != null) {
        await analytics.setUserId(id: userId);
      }

      if (userRole != null) {
        await analytics.setUserProperty(name: 'user_role', value: userRole);
      }

      if (subscriptionLevel != null) {
        await analytics.setUserProperty(name: 'subscription_level', value: subscriptionLevel);
      }
    }
  }

  // Enregistrer une erreur personnalisée dans Crashlytics
  Future<void> recordError(dynamic exception, StackTrace stack, {
    String? reason,
    bool fatal = false,
  }) async {
    if (FirebaseConfig.enableCrashlytics && !kDebugMode) {
      await FirebaseCrashlytics.instance.recordError(
        exception,
        stack,
        reason: reason,
        fatal: fatal,
      );
    } else {
      print('Erreur: $exception');
      print('Stack trace: $stack');
    }
  }

  // Ajouter des logs à un rapport de crash
  Future<void> log(String message) async {
    if (FirebaseConfig.enableCrashlytics && !kDebugMode) {
      FirebaseCrashlytics.instance.log(message);
    } else {
      print('Firebase log: $message');
    }
  }
}