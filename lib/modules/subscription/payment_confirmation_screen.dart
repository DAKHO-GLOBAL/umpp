import 'package:flutter/material.dart';
import 'package:auto_route/auto_route.dart';
import 'package:smart_turf/routes/app_router.dart';
import 'package:smart_turf/theme/app_theme.dart';

@RoutePage()
class PaymentConfirmationScreen extends StatelessWidget {
  const PaymentConfirmationScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Icône de succès
              Icon(
                Icons.check_circle_outline,
                size: 100,
                color: AppTheme.successColor,
              ),
              SizedBox(height: 32),

              // Message de confirmation
              Text(
                'Paiement confirmé !',
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: AppTheme.primaryColor,
                ),
                textAlign: TextAlign.center,
              ),
              SizedBox(height: 16),
              Text(
                'Votre abonnement a été activé avec succès.',
                style: Theme.of(context).textTheme.bodyLarge,
                textAlign: TextAlign.center,
              ),
              SizedBox(height: 8),
              Text(
                'Vous pouvez maintenant profiter de toutes les fonctionnalités premium.',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppTheme.textSecondaryColor,
                ),
                textAlign: TextAlign.center,
              ),
              SizedBox(height: 32),

              // Détails de la transaction
              Container(
                padding: EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Column(
                  children: [
                    _buildTransactionDetail('Référence', 'REF-123456789'),
                    Divider(),
                    _buildTransactionDetail('Date', _formatDateTime(DateTime.now())),
                    Divider(),
                    _buildTransactionDetail('Statut', 'Complété'),
                    Divider(),
                    _buildTransactionDetail('Méthode', 'Carte bancaire'),
                  ],
                ),
              ),
              Spacer(),

              // Bouton pour retourner à l'accueil
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {
                    context.router.push(const HomeRoute());
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.primaryColor,
                    padding: EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: Text(
                    'Retour à l\'accueil',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
              SizedBox(height: 16),

              // Lien pour voir les détails de la transaction
              TextButton(
                onPressed: () {
                  // Naviguer vers la page détaillée des transactions
                },
                child: Text('Voir les détails de la transaction'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTransactionDetail(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(
              color: Colors.grey,
            ),
          ),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  String _formatDateTime(DateTime dateTime) {
    return '${dateTime.day.toString().padLeft(2, '0')}/${dateTime.month.toString().padLeft(2, '0')}/${dateTime.year} ${dateTime.hour.toString().padLeft(2, '0')}:${dateTime.minute.toString().padLeft(2, '0')}';
  }
}