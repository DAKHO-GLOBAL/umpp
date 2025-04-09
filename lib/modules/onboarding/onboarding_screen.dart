// lib/modules/onboarding/onboarding_screen.dart
import 'package:flutter/material.dart';
import 'package:auto_route/auto_route.dart';
import 'package:smart_turf/routes/app_router.dart';
import 'package:smart_turf/theme/app_theme.dart';
import 'package:smart_turf/core/widgets/custom_button.dart';

@RoutePage()
class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({Key? key}) : super(key: key);

  @override
  _OnboardingScreenState createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  final List<Map<String, dynamic>> _onboardingData = [
    {
      'title': 'Bienvenue sur SmartTurf',
      'description': 'L\'application qui révolutionne les prédictions hippiques grâce à l\'intelligence artificielle.',
      'image': 'assets/images/onboarding1.png',
      'icon': Icons.sports_score,
    },
    {
      'title': 'Prédictions précises',
      'description': 'Obtenez des prédictions basées sur des analyses avancées de données et des algorithmes sophistiqués.',
      'image': 'assets/images/onboarding2.png',
      'icon': Icons.analytics,
    },
    {
      'title': 'Simulations personnalisées',
      'description': 'Créez vos propres scénarios et testez différentes stratégies pour maximiser vos chances.',
      'image': 'assets/images/onboarding3.png',
      'icon': Icons.tune,
    },
  ];

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: PageView.builder(
                controller: _pageController,
                itemCount: _onboardingData.length,
                onPageChanged: (index) {
                  setState(() {
                    _currentPage = index;
                  });
                },
                itemBuilder: (context, index) {
                  return _buildPage(
                    title: _onboardingData[index]['title'],
                    description: _onboardingData[index]['description'],
                    image: _onboardingData[index]['image'],
                    icon: _onboardingData[index]['icon'],
                  );
                },
              ),
            ),
            // Indicateurs de page
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(
                _onboardingData.length,
                    (index) => Container(
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  width: 10,
                  height: 10,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: _currentPage == index
                        ? AppTheme.primaryColor
                        : Colors.grey.shade300,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 20),
            // Boutons de navigation
            Padding(
              padding: const EdgeInsets.all(24.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _currentPage > 0
                      ? TextButton(
                    onPressed: () {
                      _pageController.previousPage(
                        duration: const Duration(milliseconds: 300),
                        curve: Curves.easeInOut,
                      );
                    },
                    child: const Text('Précédent'),
                  )
                      : const SizedBox(width: 80),
                  _currentPage == _onboardingData.length - 1
                      ? CustomButton(
                    text: 'Commencer',
                    onPressed: () {
                      context.router.replace(const LoginRoute());
                    },
                  )
                      : CustomButton(
                    text: 'Suivant',
                    onPressed: () {
                      _pageController.nextPage(
                        duration: const Duration(milliseconds: 300),
                        curve: Curves.easeInOut,
                      );
                    },
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildPage({
    required String title,
    required String description,
    required String image,
    required IconData icon,
  }) {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Image ou icône
          Image.asset(
            image,
            height: 200,
            errorBuilder: (context, error, stackTrace) =>
                Icon(icon, size: 150, color: AppTheme.primaryColor),
          ),
          const SizedBox(height: 40),
          // Titre
          Text(
            title,
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: AppTheme.primaryColor,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 20),
          // Description
          Text(
            description,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: AppTheme.textSecondaryColor,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}