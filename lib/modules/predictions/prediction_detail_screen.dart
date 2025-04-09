import 'package:flutter/material.dart';
import 'package:auto_route/auto_route.dart';
import 'package:smart_turf/theme/app_theme.dart';

@RoutePage()
class PredictionDetailScreen extends StatelessWidget {
  final int id;

  const PredictionDetailScreen({
    Key? key,
    @PathParam('id') required this.id,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Détail de la prédiction'),
        backgroundColor: AppTheme.primaryColor,
      ),
      body: Center(
        child: Text('Détail de la prédiction #$id - À venir'),
      ),
    );
  }
}