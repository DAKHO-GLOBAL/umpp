import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:smart_turf/config/firebase_config.dart';

class FirebaseMessagingService {
  static final FirebaseMessagingService _instance = FirebaseMessagingService._internal();

  factory FirebaseMessagingService() {
    return _instance;
  }

  FirebaseMessagingService._internal();

  final FirebaseMessaging _firebaseMessaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _flutterLocalNotificationsPlugin = FlutterLocalNotificationsPlugin();

  Future<void> initialize() async {
    if (!FirebaseConfig.enableNotifications) {
      return;
    }

    // Demander l'autorisation pour les notifications
    await _requestPermission();

    // Configurer les notifications en arrière-plan
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

    // Initialiser les notifications locales
    await _initializeLocalNotifications();

    // Configurer les gestionnaires de notifications
    _setupNotificationHandlers();

    // S'abonner au sujet par défaut
    await subscribeToTopic(FirebaseConfig.defaultFcmTopic);
  }

  Future<void> _requestPermission() async {
    final settings = await _firebaseMessaging.requestPermission(
      alert: true,
      announcement: false,
      badge: true,
      carPlay: false,
      criticalAlert: false,
      provisional: false,
      sound: true,
    );

    print('Notification permission status: ${settings.authorizationStatus}');
  }

  Future<void> _initializeLocalNotifications() async {
    const initializationSettingsAndroid = AndroidInitializationSettings('@mipmap/ic_launcher');
    const initializationSettingsIOS = DarwinInitializationSettings(
      requestSoundPermission: true,
      requestBadgePermission: true,
      requestAlertPermission: true,
    );

    const initializationSettings = InitializationSettings(
      android: initializationSettingsAndroid,
      iOS: initializationSettingsIOS,
    );

    await _flutterLocalNotificationsPlugin.initialize(
      initializationSettings,
      onDidReceiveNotificationResponse: _onDidReceiveNotificationResponse,
    );
  }

  void _setupNotificationHandlers() {
    // Gérer les messages en premier plan
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      print('Notification reçue en premier plan: ${message.notification?.title}');
      _showLocalNotification(message);
    });

    // Gérer les notifications ouvertes lorsque l'application est en arrière-plan
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      print('Notification ouverte depuis l\'arrière-plan: ${message.notification?.title}');
      _handleNotificationTap(message);
    });

    // Vérifier si l'application a été ouverte à partir d'une notification
    _firebaseMessaging.getInitialMessage().then((RemoteMessage? message) {
      if (message != null) {
        print('Application ouverte à partir d\'une notification: ${message.notification?.title}');
        _handleNotificationTap(message);
      }
    });
  }

  void _showLocalNotification(RemoteMessage message) {
    if (message.notification == null) {
      return;
    }

    final notification = message.notification!;

    const androidDetails = AndroidNotificationDetails(
      'default_channel',
      'Default Channel',
      channelDescription: 'Channel for default notifications',
      importance: Importance.max,
      priority: Priority.high,
      showWhen: true,
    );

    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );

    const notificationDetails = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );

    _flutterLocalNotificationsPlugin.show(
      notification.hashCode,
      notification.title,
      notification.body,
      notificationDetails,
      payload: message.data.toString(),
    );
  }

  void _handleNotificationTap(RemoteMessage message) {
    // Extraire les données utiles de la notification
    final data = message.data;

    // Traiter les différents types de notifications
    if (data.containsKey('type')) {
      final type = data['type'];

      switch (type) {
        case 'prediction':
        // Naviguer vers la page de prédiction
        // navigatorKey.currentState?.pushNamed('/predictions/${data['prediction_id']}');
          break;
        case 'course':
        // Naviguer vers la page de course
        // navigatorKey.currentState?.pushNamed('/courses/${data['course_id']}');
          break;
        case 'subscription':
        // Naviguer vers la page d'abonnement
        // navigatorKey.currentState?.pushNamed('/subscriptions');
          break;
        default:
        // Naviguer vers la page d'accueil par défaut
        // navigatorKey.currentState?.pushNamed('/home');
          break;
      }
    }
  }

  void _onDidReceiveNotificationResponse(NotificationResponse response) {
    // Traiter la réponse de notification locale
    print('Notification locale touchée: ${response.payload}');

    // Naviguer vers la page appropriée en fonction du payload
    if (response.payload != null) {
      // Implémenter la navigation ici
    }
  }

  // Obtenir le token FCM actuel
  Future<String?> getToken() async {
    if (!FirebaseConfig.enableNotifications) {
      return null;
    }

    return await _firebaseMessaging.getToken();
  }

  // S'abonner à un sujet/topic
  Future<void> subscribeToTopic(String topic) async {
    if (!FirebaseConfig.enableNotifications) {
      return;
    }

    await _firebaseMessaging.subscribeToTopic(topic);
    print('Abonné au topic: $topic');
  }

  // Se désabonner d'un sujet/topic
  Future<void> unsubscribeFromTopic(String topic) async {
    if (!FirebaseConfig.enableNotifications) {
      return;
    }

    await _firebaseMessaging.unsubscribeFromTopic(topic);
    print('Désabonné du topic: $topic');
  }
}

// Handler pour les messages en arrière-plan
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  // Ceci doit être implémenté de manière minimale car il s'exécute en dehors du contexte Flutter
  print('Notification reçue en arrière-plan: ${message.notification?.title}');

  // Ne pas utiliser de code complexe ici, pas de navigation ou d'UI
}