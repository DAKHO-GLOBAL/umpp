import 'dart:async';
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
class VerifyPhoneScreen extends StatefulWidget {
  final String phoneNumber;

  const VerifyPhoneScreen({
    Key? key,
    @PathParam('phone') this.phoneNumber = '',
  }) : super(key: key);

  @override
  _VerifyPhoneScreenState createState() => _VerifyPhoneScreenState();
}

class _VerifyPhoneScreenState extends State<VerifyPhoneScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();
  final _otpController = TextEditingController();

  bool _isLoading = false;
  bool _codeSent = false;
  String? _verificationId;
  int _resendCooldown = 0;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _phoneController.text = widget.phoneNumber;
  }

  @override
  void dispose() {
    _phoneController.dispose();
    _otpController.dispose();
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

  Future<void> _sendVerificationCode() async {
    if (_formKey.currentState?.validate() != true) {
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);

      // Envoyer la demande de vérification du numéro de téléphone
      await authProvider.verifyPhoneNumber(
        phoneNumber: _phoneController.text.trim(),
        onCodeSent: (verificationId, resendToken) {
          setState(() {
            _verificationId = verificationId;
            _codeSent = true;
            _isLoading = false;
          });
          _startResendCooldown();
        },
        onVerificationCompleted: (message) {
          // Cette fonction est appelée si la vérification est automatique
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(message),
                backgroundColor: AppTheme.successColor,
              ),
            );
            context.router.replace(const HomeRoute());
          }
        },
        onVerificationFailed: (error) {
          setState(() {
            _isLoading = false;
          });
          if (context.mounted) {
            ErrorDialog.show(
              context,
              message: error,
            );
          }
        },
        onCodeAutoRetrievalTimeout: () {
          setState(() {
            _isLoading = false;
          });
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('Le délai pour la récupération automatique du code a expiré. Veuillez saisir le code manuellement.'),
                backgroundColor: AppTheme.warningColor,
              ),
            );
          }
        },
      );
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      if (context.mounted) {
        ErrorDialog.show(
          context,
          message: e.toString(),
        );
      }
    }
  }

  Future<void> _verifyCode() async {
    if (_otpController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Veuillez saisir le code OTP'),
          backgroundColor: AppTheme.errorColor,
        ),
      );
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);

      if (_verificationId != null) {
        final success = await authProvider.verifyOtp(
          _verificationId!,
          _otpController.text.trim(),
        );

        if (success) {
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('Numéro de téléphone vérifié avec succès'),
                backgroundColor: AppTheme.successColor,
              ),
            );
            context.router.replace(const HomeRoute());
          }
        } else {
          if (context.mounted) {
            ErrorDialog.show(
              context,
              message: authProvider.errorMessage ?? 'Erreur lors de la vérification du code',
            );
          }
        }
      } else {
        if (context.mounted) {
          ErrorDialog.show(
            context,
            message: 'ID de vérification non disponible. Veuillez réessayer.',
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
        title: Text('Vérification du téléphone'),
        centerTitle: true,
        elevation: 0,
        backgroundColor: Colors.transparent,
        foregroundColor: AppTheme.textPrimaryColor,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Form(
            key: _formKey,
            child: _codeSent ? _buildVerificationStep() : _buildPhoneStep(),
          ),
        ),
      ),
    );
  }

  Widget _buildPhoneStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // En-tête
        Text(
          'Vérification du numéro',
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: AppTheme.primaryColor,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Nous allons envoyer un code par SMS pour vérifier votre numéro de téléphone',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: AppTheme.textSecondaryColor,
          ),
        ),
        const SizedBox(height: 32),

        // Champ numéro de téléphone
        CustomTextField(
          label: 'Numéro de téléphone',
          hintText: '+XXX XXXXXXXXX',
          controller: _phoneController,
          keyboardType: TextInputType.phone,
          textInputAction: TextInputAction.done,
          validator: Validators.validatePhoneNumber,
        ),
        const SizedBox(height: 32),

        // Bouton d'envoi
        CustomButton(
          text: 'Envoyer le code',
          onPressed: _sendVerificationCode,
          isLoading: _isLoading,
          width: double.infinity,
        ),

        // Texte informatif
        Expanded(
          child: Align(
            alignment: Alignment.bottomCenter,
            child: Padding(
              padding: const EdgeInsets.only(bottom: 16.0),
              child: Text(
                'Des frais standards de messagerie peuvent s\'appliquer.',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppTheme.textSecondaryColor,
                ),
                textAlign: TextAlign.center,
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildVerificationStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // En-tête
        Text(
          'Saisissez le code',
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: AppTheme.primaryColor,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Nous avons envoyé un code de vérification au ${_phoneController.text}',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: AppTheme.textSecondaryColor,
          ),
        ),
        const SizedBox(height: 32),

        // Champ OTP
        CustomTextField(
          label: 'Code de vérification',
          hintText: 'Entrez le code à 6 chiffres',
          controller: _otpController,
          keyboardType: TextInputType.number,
          textInputAction: TextInputAction.done,
          validator: Validators.validateOtp,
        ),
        const SizedBox(height: 32),

        // Bouton de vérification
        CustomButton(
          text: 'Vérifier',
          onPressed: _verifyCode,
          isLoading: _isLoading,
          width: double.infinity,
        ),
        const SizedBox(height: 16),

        // Bouton de renvoi
        Center(
          child: TextButton(
            onPressed: _resendCooldown > 0 ? null : _sendVerificationCode,
            child: Text(
              _resendCooldown > 0
                  ? 'Renvoyer le code (${_resendCooldown}s)'
                  : 'Renvoyer le code',
              style: TextStyle(
                color: _resendCooldown > 0
                    ? AppTheme.textSecondaryColor
                    : AppTheme.primaryColor,
              ),
            ),
          ),
        ),

        // Options supplémentaires
        Expanded(
          child: Align(
            alignment: Alignment.bottomCenter,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextButton(
                  onPressed: () {
                    setState(() {
                      _codeSent = false;
                      _verificationId = null;
                    });
                  },
                  child: Text('Modifier le numéro de téléphone'),
                ),
                const SizedBox(height: 8),
                TextButton(
                  onPressed: () {
                    context.router.replace(const HomeRoute());
                  },
                  child: Text(
                    'Vérifier plus tard',
                    style: TextStyle(color: AppTheme.textSecondaryColor),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}