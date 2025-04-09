import 'package:flutter/material.dart';
import 'package:smart_turf/core/widgets/custom_button.dart';
import 'package:smart_turf/theme/app_theme.dart';

class ErrorDialog extends StatelessWidget {
  final String title;
  final String message;
  final String buttonText;
  final VoidCallback? onButtonPressed;
  final bool showCloseButton;

  const ErrorDialog({
    Key? key,
    this.title = 'Erreur',
    required this.message,
    this.buttonText = 'OK',
    this.onButtonPressed,
    this.showCloseButton = true,
  }) : super(key: key);

  // Méthode statique pour afficher facilement
  static Future<void> show(
      BuildContext context, {
        String title = 'Erreur',
        required String message,
        String buttonText = 'OK',
        VoidCallback? onButtonPressed,
        bool showCloseButton = true,
      }) async {
    return showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => ErrorDialog(
        title: title,
        message: message,
        buttonText: buttonText,
        onButtonPressed: onButtonPressed,
        showCloseButton: showCloseButton,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16.0),
      ),
      title: Row(
        children: [
          Icon(
            Icons.error_outline,
            color: AppTheme.errorColor,
          ),
          SizedBox(width: 8.0),
          Text(title),
          Spacer(),
          if (showCloseButton)
            IconButton(
              icon: Icon(Icons.close),
              onPressed: () => Navigator.of(context).pop(),
              splashRadius: 20.0,
            ),
        ],
      ),
      content: Text(
        message,
        style: Theme.of(context).textTheme.bodyMedium,
      ),
      actions: [
        CustomButton(
          text: buttonText,
          onPressed: onButtonPressed ?? () => Navigator.of(context).pop(),
          width: double.infinity,
        ),
      ],
      actionsPadding: EdgeInsets.all(16.0),
    );
  }
}

class InfoDialog extends StatelessWidget {
  final String title;
  final String message;
  final String buttonText;
  final VoidCallback? onButtonPressed;
  final bool showCloseButton;
  final IconData icon;
  final Color iconColor;

  const InfoDialog({
    Key? key,
    required this.title,
    required this.message,
    this.buttonText = 'OK',
    this.onButtonPressed,
    this.showCloseButton = true,
    this.icon = Icons.info_outline,
    this.iconColor = AppTheme.infoColor,
  }) : super(key: key);

  // Méthode statique pour afficher facilement
  static Future<void> show(
      BuildContext context, {
        required String title,
        required String message,
        String buttonText = 'OK',
        VoidCallback? onButtonPressed,
        bool showCloseButton = true,
        IconData icon = Icons.info_outline,
        Color iconColor = AppTheme.infoColor,
      }) async {
    return showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => InfoDialog(
        title: title,
        message: message,
        buttonText: buttonText,
        onButtonPressed: onButtonPressed,
        showCloseButton: showCloseButton,
        icon: icon,
        iconColor: iconColor,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16.0),
      ),
      title: Row(
        children: [
          Icon(
            icon,
            color: iconColor,
          ),
          SizedBox(width: 8.0),
          Text(title),
          Spacer(),
          if (showCloseButton)
            IconButton(
              icon: Icon(Icons.close),
              onPressed: () => Navigator.of(context).pop(),
              splashRadius: 20.0,
            ),
        ],
      ),
      content: Text(
        message,
        style: Theme.of(context).textTheme.bodyMedium,
      ),
      actions: [
        CustomButton(
          text: buttonText,
          onPressed: onButtonPressed ?? () => Navigator.of(context).pop(),
          width: double.infinity,
        ),
      ],
      actionsPadding: EdgeInsets.all(16.0),
    );
  }
}