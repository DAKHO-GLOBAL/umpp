import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:smart_turf/theme/app_theme.dart';

class CustomTextField extends StatefulWidget {
  final String label;
  final String? labelText;
  final String? hintText;
  final TextEditingController? controller;
  final FocusNode? focusNode;
  final TextInputType keyboardType;
  final TextInputAction textInputAction;
  final bool obscureText;
  final String? Function(String?)? validator;
  final Function(String)? onChanged;
  final Function(String)? onSubmitted;
  final List<TextInputFormatter>? inputFormatters;
  final bool enabled;
  final int? maxLines;
  final int? minLines;
  final Widget? prefix;
  final Widget? suffix;
  final IconData? prefixIcon;
  final IconData? suffixIcon;
  final String? prefixText;
  final String? suffixText;
  final String? errorText;
  final EdgeInsetsGeometry? contentPadding;
  final Color? fillColor;
  final bool isFullWidth;

  const CustomTextField({
    Key? key,
    required this.label,
    this.labelText,
    this.hintText,
    this.controller,
    this.focusNode,
    this.keyboardType = TextInputType.text,
    this.textInputAction = TextInputAction.next,
    this.obscureText = false,
    this.validator,
    this.onChanged,
    this.onSubmitted,
    this.inputFormatters,
    this.enabled = true,
    this.maxLines = 1,
    this.minLines,
    this.prefix,
    this.suffix,
    this.prefixIcon,
    this.suffixIcon,
    this.prefixText,
    this.suffixText,
    this.errorText,
    this.contentPadding,
    this.fillColor,
    this.isFullWidth = false,
  }) : super(key: key);

  @override
  State<CustomTextField> createState() => _CustomTextFieldState();
}

class _CustomTextFieldState extends State<CustomTextField> {
  bool _passwordVisible = false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    Widget? suffixWidget = widget.suffix;
    if (widget.obscureText && suffixWidget == null) {
      suffixWidget = GestureDetector(
        onTap: () {
          setState(() {
            _passwordVisible = !_passwordVisible;
          });
        },
        child: Icon(
          _passwordVisible ? Icons.visibility_off : Icons.visibility,
          color: AppTheme.textSecondaryColor,
        ),
      );
    } else if (widget.suffixIcon != null && suffixWidget == null) {
      suffixWidget = Icon(widget.suffixIcon, color: AppTheme.textSecondaryColor);
    }

    Widget? prefixWidget = widget.prefix;
    if (widget.prefixIcon != null && prefixWidget == null) {
      prefixWidget = Icon(widget.prefixIcon, color: AppTheme.textSecondaryColor);
    }

    Widget textField = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (widget.label.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(bottom: 8.0),
            child: Text(
              widget.label,
              style: theme.textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w500,
                color: AppTheme.textPrimaryColor,
              ),
            ),
          ),
        TextFormField(
          controller: widget.controller,
          focusNode: widget.focusNode,
          keyboardType: widget.keyboardType,
          textInputAction: widget.textInputAction,
          obscureText: widget.obscureText && !_passwordVisible,
          validator: widget.validator,
          onChanged: widget.onChanged,
          onFieldSubmitted: widget.onSubmitted,
          inputFormatters: widget.inputFormatters,
          enabled: widget.enabled,
          maxLines: widget.obscureText ? 1 : widget.maxLines,
          minLines: widget.minLines,
          decoration: InputDecoration(
            labelText: widget.labelText,
            hintText: widget.hintText,
            errorText: widget.errorText,
            prefixIcon: prefixWidget,
            suffixIcon: suffixWidget,
            prefixText: widget.prefixText,
            suffixText: widget.suffixText,
            filled: true,
            fillColor: widget.fillColor ?? AppTheme.surfaceColor,
            contentPadding: widget.contentPadding ??
                const EdgeInsets.symmetric(horizontal: 16.0, vertical: 14.0),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8.0),
              borderSide: BorderSide.none,
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8.0),
              borderSide: BorderSide.none,
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8.0),
              borderSide: BorderSide(color: AppTheme.primaryColor, width: 1.5),
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8.0),
              borderSide: BorderSide(color: AppTheme.errorColor, width: 1.5),
            ),
            focusedErrorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8.0),
              borderSide: BorderSide(color: AppTheme.errorColor, width: 1.5),
            ),
          ),
        ),
      ],
    );

    return widget.isFullWidth
        ? textField
        : ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 400),
      child: textField,
    );
  }
}
