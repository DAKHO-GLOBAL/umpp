import 'package:flutter/material.dart';
import 'package:smart_turf/theme/app_theme.dart';

class CustomButton extends StatelessWidget {
  final String text;
  //final VoidCallback onPressed;
  final VoidCallback? onPressed;

  final bool isLoading;
  final bool isOutlined;
  final Color? backgroundColor;
  final Color? textColor;
  final double? width;
  final double height;
  final double borderRadius;
  final EdgeInsets padding;
  final IconData? iconData;
  final bool iconOnRight;

  const CustomButton({
    Key? key,
    required this.text,
    required this.onPressed,
    this.isLoading = false,
    this.isOutlined = false,
    this.backgroundColor,
    this.textColor,
    this.width,
    this.height = 48.0,
    this.borderRadius = 8.0,
    this.padding = const EdgeInsets.symmetric(horizontal: 16.0),
    this.iconData,
    this.iconOnRight = false,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    // Déterminer les couleurs en fonction du thème et des paramètres
    final bgColor = backgroundColor ??
        (isOutlined ? Colors.transparent : AppTheme.primaryColor);
    final txtColor = textColor ??
        (isOutlined ? AppTheme.primaryColor : Colors.white);

    Widget buttonContent;

    if (isLoading) {
      buttonContent = SizedBox(
        height: 20,
        width: 20,
        child: CircularProgressIndicator(
          valueColor: AlwaysStoppedAnimation<Color>(txtColor),
          strokeWidth: 2.0,
        ),
      );
    } else if (iconData != null) {
      final icon = Icon(iconData, color: txtColor, size: 20);
      final textWidget = Text(
        text,
        style: theme.textTheme.labelLarge?.copyWith(color: txtColor),
      );

      buttonContent = Row(
        mainAxisSize: MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.center,
        children: iconOnRight
            ? [textWidget, SizedBox(width: 8), icon]
            : [icon, SizedBox(width: 8), textWidget],
      );
    } else {
      buttonContent = Text(
        text,
        style: theme.textTheme.labelLarge?.copyWith(color: txtColor),
      );
    }

    // Widget final du bouton
    return SizedBox(
      width: width,
      height: height,
      child: isOutlined
          ? OutlinedButton(
        onPressed: isLoading ? null : onPressed,
        style: OutlinedButton.styleFrom(
          side: BorderSide(color: AppTheme.primaryColor, width: 1.5),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(borderRadius),
          ),
          padding: padding,
        ),
        child: buttonContent,
      )
          : ElevatedButton(
        onPressed: isLoading ? null : onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: bgColor,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(borderRadius),
          ),
          padding: padding,
        ),
        child: buttonContent,
      ),
    );
  }
}