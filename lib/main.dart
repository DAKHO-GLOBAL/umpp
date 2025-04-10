import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:smart_turf/config/api_config.dart';
import 'package:smart_turf/config/app_theme.dart';
import 'package:smart_turf/providers/auth_provider.dart';
import 'package:smart_turf/screens/home_screen.dart';
import 'package:smart_turf/screens/login_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
      ],
      child: MaterialApp(
        title: AppConfig.appName,
        theme: AppTheme.lightTheme,
        home: const AuthenticationWrapper(),
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}

class AuthenticationWrapper extends StatelessWidget {
  const AuthenticationWrapper({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);

    // Afficher un indicateur de chargement pendant la vérification de l'authentification
    if (authProvider.isLoading) {
      return const Scaffold(
        body: Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    // Rediriger vers l'écran approprié en fonction de l'état d'authentification
    if (authProvider.isAuthenticated) {
      return const HomeScreen();
    } else {
      return const LoginScreen();
    }
  }
}