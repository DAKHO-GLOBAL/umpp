import 'package:flutter/material.dart';
import 'package:auto_route/auto_route.dart';
import 'package:smart_turf/theme/app_theme.dart';

@RoutePage()
class PredictionsScreen extends StatelessWidget {
  const PredictionsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Prédictions'),
        backgroundColor: AppTheme.primaryColor,
      ),
      body: Center(
        child: Text('Predictions Screen - À venir'),
      ),
    );
  }
}