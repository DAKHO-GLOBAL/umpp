import 'dart:async';
import 'package:flutter/material.dart';
import 'package:auto_route/auto_route.dart';
import 'package:provider/provider.dart';
import 'package:smart_turf/core/constants/app_constants.dart';
import 'package:smart_turf/core/widgets/custom_button.dart';
import 'package:smart_turf/core/widgets/error_dialog.dart';
import 'package:smart_turf/data/providers/auth_provider.dart';
import 'package:smart_turf/routes/app_router.dart';
import 'package:smart_turf/theme/app_theme.dart';

@RoutePage()
class VerifyEmailScreen extends StatefulWidget {
  const VerifyEmailScreen({Key? key}) : super(key: key);

  @override
  _VerifyEmailScreenState createState() => _VerifyEmailScreenState();
}

class _VerifyEmailScreenState extends State<VerifyEmailScreen> {
  bool _isLoading = false;
  int _resendCooldown = 0;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _checkVerificationStatus();
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void _startResendCooldown() {
    setState(() {
      _resendCooldown = 60;
    });

    _timer = Timer.periodic(Duration(seconds: 1), (timer) {
      setState(() {
        if (_resendCooldown > 0) {
          _resendCooldown--;
        } else {
          _timer?.cancel();
        }
      });
    });
  }

  Future<void> _sendVerificationEmail() async {
    if (_resendCooldown > 0) {
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final success = await authProvider.sendEmailVerification();

      if (success) {
        _startResendCooldown();
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Email de vérification envoyé. Veuillez vérifier votre boîte de réception.'),
              backgroundColor: AppTheme.successColor,
            ),
          );
        }
      } else {
        if (context.mounted) {
          ErrorDialog.show(
            context,
            message: authProvider.errorMessage ?? 'Erreur lors de l\'envoi de l\'email de vérification.',
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

  Future<void> _checkVerificationStatus() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      await authProvider.loadUserProfile();

      // Si l'email est vérifié, rediriger vers l'écran d'accueil
      if (authProvider.isEmailVerified) {
        if (context.mounted) {
          context.router.replace(const HomeRoute());
        }
      }
    } catch (e) {
      print('Error checking verification status: $e');
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _logout() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      await authProvider.logout();

      if (context.mounted) {
        context.router.replace(const LoginRoute());
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
    final authProvider = Provider.of<AuthProvider>(context);
    final userEmail = authProvider.currentUser?.email ?? '';

    return Scaffold(
      appBar: AppBar(
        title: Text('Vérification de l\'email'),
        centerTitle: true,
        elevation: 0,
        backgroundColor: Colors.transparent,
        foregroundColor: AppTheme.textPrimaryColor,
        automaticallyImplyLeading: false,
        actions: [
          IconButton(
            icon: Icon(Icons.logout),
            onPressed: _logout,
            tooltip: 'Déconnexion',
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Icône
              Icon(
                Icons.mark_email_unread_outlined,
                size: 80,
                color: AppTheme.primaryColor,
              ),
              const SizedBox(height: 32),

              // Titre
              Text(
                'Vérifiez votre email',
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: AppTheme.primaryColor,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),

              // Instructions
              Text(
                'Nous avons envoyé un lien de vérification à :',
                style: Theme.of(context).textTheme.bodyLarge,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                userEmail,
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              Text(
                'Veuillez vérifier votre boîte de réception et cliquer sur le lien pour activer votre compte.',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppTheme.textSecondaryColor,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 32),

              // Bouton pour vérifier le statut
              CustomButton(
                text: 'J\'ai vérifié mon email',
                onPressed: _checkVerificationStatus,
                isLoading: _isLoading,
                width: double.infinity,
              ),
              const SizedBox(height: 16),

              // Bouton pour renvoyer l'email
              CustomButton(
                text: _resendCooldown > 0
                    ? 'Renvoyer l\'email (${_resendCooldown}s)'
                    : 'Renvoyer l\'email',
                onPressed: _resendCooldown > 0 ? null : _sendVerificationEmail,
                isOutlined: true,
                width: double.infinity,
              ),
              const SizedBox(height: 24),

              // Texte d'aide
              Text(
                'Vous n\'avez pas reçu d\'email ? Vérifiez vos spams ou contactez le support.',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppTheme.textSecondaryColor,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}