import 'package:flutter/material.dart';
import 'package:auto_route/auto_route.dart';
import 'package:smart_turf/routes/app_router.dart';
import 'package:smart_turf/theme/app_theme.dart';

@RoutePage()
class SubscriptionsScreen extends StatelessWidget {
  const SubscriptionsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Abonnements'),
        backgroundColor: AppTheme.primaryColor,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Choisissez votre formule',
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Accédez à toutes nos fonctionnalités premium',
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: AppTheme.textSecondaryColor,
              ),
            ),
            SizedBox(height: 24),

            // Plans d'abonnement
            Expanded(
              child: ListView(
                children: [
                  // Plan Standard
                  _buildSubscriptionCard(
                    context,
                    title: 'Standard',
                    price: '9.99',
                    features: [
                      'Prédictions Top 3',
                      'Simulations basiques',
                      '30 prédictions par jour',
                      '15 simulations par jour',
                    ],
                    onSubscribe: () {
                      context.router.push(PaymentRoute(plan: 'standard'));
                    },
                  ),
                  SizedBox(height: 16),

                  // Plan Premium
                  _buildSubscriptionCard(
                    context,
                    title: 'Premium',
                    price: '19.99',
                    isRecommended: true,
                    features: [
                      'Prédictions Top 3 et Top 7',
                      'Simulations avancées',
                      'Prédictions illimitées',
                      'Simulations illimitées',
                      'Notifications personnalisées',
                    ],
                    onSubscribe: () {
                      context.router.push(PaymentRoute(plan: 'premium'));
                    },
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSubscriptionCard(
      BuildContext context, {
        required String title,
        required String price,
        required List<String> features,
        required VoidCallback onSubscribe,
        bool isRecommended = false,
      }) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: Offset(0, 4),
          ),
        ],
        border: isRecommended
            ? Border.all(color: AppTheme.secondaryColor, width: 2)
            : null,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // En-tête du plan
          Container(
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: isRecommended
                  ? AppTheme.secondaryColor.withOpacity(0.1)
                  : AppTheme.surfaceColor,
              borderRadius: BorderRadius.only(
                topLeft: Radius.circular(16),
                topRight: Radius.circular(16),
              ),
            ),
            child: Row(
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: isRecommended
                            ? AppTheme.secondaryColor
                            : AppTheme.primaryColor,
                      ),
                    ),
                    SizedBox(height: 4),
                    RichText(
                      text: TextSpan(
                        style: Theme.of(context).textTheme.bodyLarge,
                        children: [
                          TextSpan(
                            text: '$price€',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 24,
                              color: isRecommended
                                  ? AppTheme.secondaryColor
                                  : AppTheme.primaryColor,
                            ),
                          ),
                          TextSpan(
                            text: ' / mois',
                            style: TextStyle(
                              color: AppTheme.textSecondaryColor,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                Spacer(),
                if (isRecommended)
                  Container(
                    padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppTheme.secondaryColor,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Text(
                      'Recommandé',
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 12,
                      ),
                    ),
                  ),
              ],
            ),
          ),

          // Fonctionnalités
          Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ...features.map((feature) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    children: [
                      Icon(
                        Icons.check_circle,
                        color: isRecommended
                            ? AppTheme.secondaryColor
                            : AppTheme.primaryColor,
                        size: 20,
                      ),
                      SizedBox(width: 8),
                      Text(feature),
                    ],
                  ),
                )),
              ],
            ),
          ),

          // Bouton d'abonnement
          Padding(
            padding: EdgeInsets.all(16),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: onSubscribe,
                style: ElevatedButton.styleFrom(
                  backgroundColor:
                  isRecommended ? AppTheme.secondaryColor : AppTheme.primaryColor,
                  padding: EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                child: Text(
                  'S\'abonner',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}