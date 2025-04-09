import 'package:flutter/material.dart';
import 'package:auto_route/auto_route.dart';
import 'package:smart_turf/theme/app_theme.dart';

@RoutePage()
class CoursesScreen extends StatelessWidget {
  const CoursesScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Courses'),
        backgroundColor: AppTheme.primaryColor,
      ),
      body: Center(
        child: Text('Courses Screen - À venir'),
      ),
    );
  }
}