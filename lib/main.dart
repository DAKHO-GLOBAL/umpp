import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:smart_turf/config/firebase_config.dart';
import 'package:smart_turf/routes/app_router.dart';
import 'package:smart_turf/services/firebase/firebase_service.dart';
import 'package:smart_turf/data/providers/auth_provider.dart';
import 'package:smart_turf/data/providers/user_provider.dart';
import 'package:smart_turf/theme/app_theme.dart';
import 'package:smart_turf/services/api/api_client.dart';
import 'package:smart_turf/services/local/storage_service.dart';
import 'package:smart_turf/data/repositories/auth_repository.dart';
import 'package:smart_turf/services/api/auth_api_service.dart';
import 'package:smart_turf/services/firebase/firebase_auth_service.dart';
import 'package:smart_turf/services/local/session_manager.dart';
import 'package:smart_turf/data/repositories/user_repository.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialisation des services
  final storageService = StorageService();
  await storageService.initialize();

  // Initialisation de Firebase
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );

  // Initialisation du service Firebase
  await FirebaseService().initialize();

  // Initialisation des services et repositories
  final apiClient = ApiClient(storageService);
  final authApiService = AuthApiService(apiClient);
  final firebaseAuthService = FirebaseAuthService();
  final sessionManager = SessionManager(storageService, authApiService);

  final authRepository = AuthRepository(
    authApiService,
    firebaseAuthService,
    sessionManager,
  );

  final userRepository = UserRepository(apiClient, storageService);

  runApp(MyApp(
    storageService: storageService,
    authRepository: authRepository,
    userRepository: userRepository,
  ));
}

class MyApp extends StatelessWidget {
  final StorageService storageService;
  final AuthRepository authRepository;
  final UserRepository userRepository;
  final _appRouter = AppRouter();

  MyApp({
    Key? key,
    required this.storageService,
    required this.authRepository,
    required this.userRepository,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (_) => AuthProvider(authRepository: authRepository),
        ),
        ChangeNotifierProvider(
          create: (_) => UserProvider(userRepository: userRepository),
        ),
      ],
      child: MaterialApp.router(
        title: 'SmartTurf',
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        themeMode: ThemeMode.system,
        debugShowCheckedModeBanner: false,
        routerDelegate: _appRouter.delegate(),
        routeInformationParser: _appRouter.defaultRouteParser(),
      ),
    );
  }
}