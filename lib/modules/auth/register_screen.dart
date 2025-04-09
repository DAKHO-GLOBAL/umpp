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
class RegisterScreen extends StatefulWidget {
  const RegisterScreen({Key? key}) : super(key: key);

  @override
  _RegisterScreenState createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();

  final _emailController = TextEditingController();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();

  bool _agreeToTerms = false;
  bool _isLoading = false;

  @override
  void dispose() {
    _emailController.dispose();
    _usernameController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _firstNameController.dispose();
    _lastNameController.dispose();
    super.dispose();
  }

  Future<void> _register() async {
    if (_formKey.currentState?.validate() != true) return;

    if (!_agreeToTerms) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Vous devez accepter les conditions d\'utilisation'),
          backgroundColor: AppTheme.errorColor,
        ),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final success = await authProvider.register(
        email: _emailController.text.trim(),
        password: _passwordController.text,
        username: _usernameController.text.trim(),
        firstName: _firstNameController.text.trim(),
        lastName: _lastNameController.text.trim(),
      );

      if (!success && context.mounted) {
        ErrorDialog.show(
          context,
          message: authProvider.errorMessage ?? AppConstants.errorMessage,
        );
      }
    } catch (e) {
      if (context.mounted) {
        ErrorDialog.show(context, message: e.toString());
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _registerWithGoogle() async {
    setState(() => _isLoading = true);

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
        ErrorDialog.show(context, message: e.toString());
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text('Créer un compte'),
        centerTitle: true,
        elevation: 0,
        backgroundColor: Colors.transparent,
        foregroundColor: AppTheme.textPrimaryColor,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildHeader(context),
                const SizedBox(height: 24),
                _buildGoogleButton(),
                const SizedBox(height: 20),
                _buildSeparator(context),
                const SizedBox(height: 20),
                _buildPersonalInfoFields(),
                const SizedBox(height: 24),
                _buildAccountInfoFields(),
                const SizedBox(height: 16),
                _buildTermsCheckbox(context),
                const SizedBox(height: 32),
                CustomButton(
                  text: 'S\'inscrire',
                  onPressed: _register,
                  isLoading: _isLoading,
                  width: double.infinity,
                ),
                const SizedBox(height: 24),
                _buildLoginLink(context),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Rejoignez SmartTurf',
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: AppTheme.primaryColor,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Créez votre compte pour accéder aux prédictions hippiques',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: AppTheme.textSecondaryColor,
          ),
        ),
      ],
    );
  }

  Widget _buildGoogleButton() {
    return CustomButton(
      text: 'S\'inscrire avec Google',
      onPressed: _registerWithGoogle,
      isOutlined: true,
      width: double.infinity,
      iconData: Icons.g_mobiledata,
    );
  }

  Widget _buildSeparator(BuildContext context) {
    return Row(
      children: [
        const Expanded(child: Divider()),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16.0),
          child: Text(
            'OU',
            style: TextStyle(color: AppTheme.textSecondaryColor),
          ),
        ),
        const Expanded(child: Divider()),
      ],
    );
  }

  Widget _buildPersonalInfoFields() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Informations personnelles',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 16),
        CustomTextField(
          label: 'Prénom',
          hintText: 'Votre prénom',
          controller: _firstNameController,
          textInputAction: TextInputAction.next,
        ),
        const SizedBox(height: 16),
        CustomTextField(
          label: 'Nom',
          hintText: 'Votre nom',
          controller: _lastNameController,
          textInputAction: TextInputAction.next,
        ),
      ],
    );
  }

  Widget _buildAccountInfoFields() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Informations du compte',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 16),
        CustomTextField(
          label: 'Email',
          hintText: 'Votre adresse email',
          controller: _emailController,
          keyboardType: TextInputType.emailAddress,
          textInputAction: TextInputAction.next,
          validator: Validators.validateEmail,
        ),
        const SizedBox(height: 16),
        CustomTextField(
          label: 'Nom d\'utilisateur',
          hintText: 'Choisissez un nom d\'utilisateur',
          controller: _usernameController,
          textInputAction: TextInputAction.next,
          validator: Validators.validateUsername,
        ),
        const SizedBox(height: 16),
        CustomTextField(
          label: 'Mot de passe',
          hintText: 'Choisissez un mot de passe',
          controller: _passwordController,
          obscureText: true,
          textInputAction: TextInputAction.next,
          validator: Validators.validatePassword,
        ),
        const SizedBox(height: 16),
        CustomTextField(
          label: 'Confirmer le mot de passe',
          hintText: 'Confirmez votre mot de passe',
          controller: _confirmPasswordController,
          obscureText: true,
          textInputAction: TextInputAction.done,
          validator: (value) => Validators.validateConfirmPassword(
            value,
            _passwordController.text,
          ),
        ),
      ],
    );
  }

  Widget _buildTermsCheckbox(BuildContext context) {
    return Row(
      children: [
        Checkbox(
          value: _agreeToTerms,
          onChanged: (value) {
            setState(() {
              _agreeToTerms = value ?? false;
            });
          },
          activeColor: AppTheme.primaryColor,
        ),
        Expanded(
          child: GestureDetector(
            onTap: () {
              setState(() {
                _agreeToTerms = !_agreeToTerms;
              });
            },
            child: RichText(
              text: TextSpan(
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppTheme.textPrimaryColor,
                ),
                children: [
                  const TextSpan(text: 'J\'accepte les '),
                  TextSpan(
                    text: 'Conditions d\'utilisation',
                    style: const TextStyle(
                      color: AppTheme.primaryColor,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const TextSpan(text: ' et la '),
                  TextSpan(
                    text: 'Politique de confidentialité',
                    style: const TextStyle(
                      color: AppTheme.primaryColor,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildLoginLink(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text('Déjà un compte ? ', style: Theme.of(context).textTheme.bodyMedium),
        TextButton(
          onPressed: () => context.router.replace(const LoginRoute()),
          child: const Text('Se connecter'),
        ),
      ],
    );
  }
}
