import 'package:flutter/material.dart';
import 'package:auto_route/auto_route.dart';
import 'package:provider/provider.dart';
import 'package:smart_turf/core/constants/app_constants.dart';
import 'package:smart_turf/core/utils/validators.dart';
import 'package:smart_turf/core/widgets/custom_button.dart';
import 'package:smart_turf/core/widgets/custom_text_field.dart';
import 'package:smart_turf/core/widgets/error_dialog.dart';
import 'package:smart_turf/data/providers/auth_provider.dart';
import 'package:smart_turf/routes/app_router.dart';
import 'package:smart_turf/theme/app_theme.dart';

@RoutePage()
class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _rememberMe = false;
  bool _isLoading = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (_formKey.currentState?.validate() != true) {
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final success = await authProvider.login(
        _emailController.text.trim(),
        _passwordController.text,
      );

      if (success) {
        // La redirection est gérée par AuthWrapper
      } else {
        // Afficher l'erreur
        if (context.mounted) {
          ErrorDialog.show(
            context,
            message: authProvider.errorMessage ?? AppConstants.errorMessage,
          );
        }
      }
    } catch (e) {
      if (context.mounted) {
        ErrorDialog.show(
          context,
          message: e.toString(),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _loginWithGoogle() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final success = await authProvider.loginWithGoogle();

      if (!success && context.mounted) {
        ErrorDialog.show(
          context,
          message: authProvider.errorMessage ?? 'Google sign-in failed',
        );
      }
    } catch (e) {
      if (context.mounted) {
        ErrorDialog.show(
          context,
          message: e.toString(),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24.0),
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  // Logo
                  Image.asset(
                    'assets/images/logo.png',
                    height: 120,
                  ),
                  const SizedBox(height: 24),

                  // Titre
                  Text(
                    'Bienvenue sur SmartTurf',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: AppTheme.primaryColor,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Connectez-vous pour accéder à vos prédictions hippiques',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: AppTheme.textSecondaryColor,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 32),

                  // Champ email
                  CustomTextField(
                    label: 'Email',
                    hintText: 'Votre adresse email',
                    controller: _emailController,
                    keyboardType: TextInputType.emailAddress,
                    textInputAction: TextInputAction.next,
                    validator: Validators.validateEmail,
                    prefix: Icon(Icons.email_outlined, color: AppTheme.textSecondaryColor),
                  ),
                  const SizedBox(height: 16),

                  // Champ mot de passe
                  CustomTextField(
                    label: 'Mot de passe',
                    hintText: 'Votre mot de passe',
                    controller: _passwordController,
                    obscureText: true,
                    textInputAction: TextInputAction.done,
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return 'Le mot de passe est requis';
                      }
                      return null;
                    },
                    prefix: Icon(Icons.lock_outline, color: AppTheme.textSecondaryColor),
                  ),
                  const SizedBox(height: 8),

                  // Checkbox "Se souvenir de moi" et lien "Mot de passe oublié"
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Checkbox(
                            value: _rememberMe,
                            onChanged: (value) {
                              setState(() {
                                _rememberMe = value ?? false;
                              });
                            },
                            activeColor: AppTheme.primaryColor,
                          ),
                          Text(
                            'Se souvenir de moi',
                            style: Theme.of(context).textTheme.bodyMedium,
                          ),
                        ],
                      ),
                      TextButton(
                        onPressed: () {
                          context.router.push(const PasswordResetRoute());
                        },
                        child: Text('Mot de passe oublié ?'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),

                  // Bouton de connexion
                  CustomButton(
                    text: 'Se connecter',
                    onPressed: _login,
                    isLoading: _isLoading,
                    width: double.infinity,
                  ),
                  const SizedBox(height: 16),

                  // Séparateur
                  Row(
                    children: [
                      Expanded(child: Divider()),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16.0),
                        child: Text(
                          'OU',
                          style: TextStyle(color: AppTheme.textSecondaryColor),
                        ),
                      ),
                      Expanded(child: Divider()),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // Bouton de connexion avec Google
                  CustomButton(
                    text: 'Se connecter avec Google',
                    onPressed: _loginWithGoogle,
                    isOutlined: true,
                    width: double.infinity,
                    iconData: Icons.g_mobiledata,
                  ),
                  const SizedBox(height: 24),

                  // Lien pour s'inscrire
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        'Pas encore de compte ? ',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                      TextButton(
                        onPressed: () {
                          context.router.push(const RegisterRoute());
                        },
                        child: Text('S\'inscrire'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}