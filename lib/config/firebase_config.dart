import 'package:firebase_core/firebase_core.dart';

// Ces options seraient normalement générées automatiquement par FlutterFire CLI
class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    // Configuration pour différentes plateformes
    // Ces valeurs doivent être remplacées par les vraies valeurs de configuration

    // Pour Android
    return const FirebaseOptions(
      apiKey: 'YOUR_ANDROID_API_KEY',
      appId: 'YOUR_ANDROID_APP_ID',
      messagingSenderId: 'YOUR_MESSAGING_SENDER_ID',
      projectId: 'YOUR_PROJECT_ID',
      storageBucket: 'YOUR_STORAGE_BUCKET',
    );

    // Vous pouvez ajouter des conditions pour différentes plateformes
    // if (Platform.isIOS) { ... }
    // if (Platform.isMacOS) { ... }
    // if (kIsWeb) { ... }
  }
}

// Configuration des services Firebase
class FirebaseConfig {
  // Configuration de Firebase Cloud Messaging
  static const bool enableNotifications = true;
  static const String defaultFcmTopic = 'general';

  // Configuration de Firebase Analytics
  static const bool enableAnalytics = true;
  static const int sessionTimeout = 30; // minutes

  // Configuration de Firebase Crashlytics
  static const bool enableCrashlytics = true;
  static const bool collectUserIdentifiers = false;
}