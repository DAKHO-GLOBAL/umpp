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
class PasswordResetScreen extends StatefulWidget {
  const PasswordResetScreen({Key? key}) : super(key: key);

  @override
  _PasswordResetScreenState createState() => _PasswordResetScreenState();
}

class _PasswordResetScreenState extends State<PasswordResetScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  bool _isLoading = false;
  bool _requestSent = false;

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  Future<void> _resetPassword() async {
    if (_formKey.currentState?.validate() != true) {
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final success = await authProvider.forgotPassword(_emailController.text.trim());

      if (success) {
        setState(() {
          _requestSent = true;
        });
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Réinitialisation du mot de passe'),
        centerTitle: true,
        elevation: 0,
        backgroundColor: Colors.transparent,
        foregroundColor: AppTheme.textPrimaryColor,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: _requestSent ? _buildSuccessScreen() : _buildRequestScreen(),
        ),
      ),
    );
  }

  Widget _buildRequestScreen() {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // En-tête
          Text(
            'Mot de passe oublié ?',
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: AppTheme.primaryColor,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Entrez votre adresse email pour réinitialiser votre mot de passe',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: AppTheme.textSecondaryColor,
            ),
          ),
          const SizedBox(height: 32),

          // Email
          CustomTextField(
            label: 'Email',
            hintText: 'Votre adresse email',
            controller: _emailController,
            keyboardType: TextInputType.emailAddress,
            textInputAction: TextInputAction.done,
            validator: Validators.validateEmail,
          ),
          const SizedBox(height: 32),

          // Bouton de réinitialisation
          CustomButton(
            text: 'Réinitialiser le mot de passe',
            onPressed: _resetPassword,
            isLoading: _isLoading,
            width: double.infinity,
          ),
          const SizedBox(height: 16),

          // Lien pour revenir à la connexion
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                'Vous vous souvenez de votre mot de passe ? ',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              TextButton(
                onPressed: () {
                  context.router.pop();
                },
                child: Text('Se connecter'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSuccessScreen() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        // Icône de succès
        Icon(
          Icons.check_circle_outline,
          size: 80,
          color: AppTheme.successColor,
        ),
        const SizedBox(height: 24),

        // Message de succès
        Text(
          'Email envoyé !',
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: AppTheme.primaryColor,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 16),
        Text(
          'Nous avons envoyé un lien de réinitialisation du mot de passe à ${_emailController.text}',
          style: Theme.of(context).textTheme.bodyMedium,
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 8),
        Text(
          'Veuillez vérifier votre boîte de réception et suivre les instructions.',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: AppTheme.textSecondaryColor,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 32),

        // Bouton pour revenir à la connexion
        CustomButton(
          text: 'Retour à la connexion',
          onPressed: () {
            context.router.replace(const LoginRoute());
          },
          width: double.infinity,
        ),
        const SizedBox(height: 16),

        // Lien pour renvoyer l'email
        TextButton(
          onPressed: () {
            setState(() {
              _requestSent = false;
            });
          },
          child: Text('Je n\'ai pas reçu l\'email, renvoyer'),
        ),
      ],
    );
  }
}