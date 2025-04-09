import 'package:flutter/material.dart';
import 'package:auto_route/auto_route.dart';
import 'package:smart_turf/routes/app_router.dart';
import 'package:smart_turf/theme/app_theme.dart';

@RoutePage()
class PaymentScreen extends StatefulWidget {
  final String plan;

  const PaymentScreen({
    Key? key,
    @PathParam('plan') required this.plan,
  }) : super(key: key);

  @override
  _PaymentScreenState createState() => _PaymentScreenState();
}

class _PaymentScreenState extends State<PaymentScreen> {
  String _selectedPaymentMethod = 'card';
  int _selectedDuration = 1;
  bool _isProcessing = false;

  @override
  Widget build(BuildContext context) {
    // Prix selon le plan
    final double basePrice = widget.plan == 'premium' ? 19.99 : 9.99;

    // Prix selon la durée sélectionnée avec réduction
    double finalPrice;
    if (_selectedDuration == 12) {
      finalPrice = basePrice * 12 * 0.75; // 25% de réduction
    } else if (_selectedDuration == 6) {
      finalPrice = basePrice * 6 * 0.85; // 15% de réduction
    } else if (_selectedDuration == 3) {
      finalPrice = basePrice * 3 * 0.9; // 10% de réduction
    } else {
      finalPrice = basePrice;
    }

    return Scaffold(
      appBar: AppBar(
        title: Text('Paiement'),
        backgroundColor: AppTheme.primaryColor,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
        // Résumé de l'abonnement
        Card(
        shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Résumé de votre abonnement',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Plan'),
                Text(
                  widget.plan.capitalize(),
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Durée'),
                Text(
                  _selectedDuration == 1
                      ? '1 mois'
                      : '$_selectedDuration mois',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Prix'),
                Text(
                  '${finalPrice.toStringAsFixed(2)}€',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 18,
                    color: AppTheme.primaryColor,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    ),
    SizedBox(height: 24),

    // Sélection de la durée
    Text(
    'Choisissez la durée',
    style: Theme.of(context).textTheme.titleMedium?.copyWith(
    fontWeight: FontWeight.bold,
    ),
    ),
    SizedBox(height: 8),
    Row(
    children: [
    Expanded(
    child: _buildDurationOption(1, 'Mensuel', basePrice, 0),
    ),
    SizedBox(width: 8),
    Expanded(
    child: _buildDurationOption(3, '3 mois', basePrice * 3, 10),
    ),
    SizedBox(width: 8),
    Expanded(
    child: _buildDurationOption(6, '6 mois', basePrice * 6, 15),
    ),
    SizedBox(width: 8),
    Expanded(
    child: _buildDurationOption(12, '1 an', basePrice * 12, 25),
    ),
    ],
    ),
    SizedBox(height: 24),

    // Sélection du mode de paiement
    Text(
    'Méthode de paiement',
    style: Theme.of(context).textTheme.titleMedium?.copyWith(
    fontWeight: FontWeight.bold,
    ),
    ),
    SizedBox(height: 8),
    _buildPaymentMethodSelector('card', 'Carte bancaire', Icons.credit_card),
    SizedBox(height: 8),
    _buildPaymentMethodSelector('orange', 'Orange Money', Icons.phone_android),
    SizedBox(height: 8),
    _buildPaymentMethodSelector('manual', 'Paiement manuel', Icons.receipt),

    // Bouton de paiement
    Spacer(),
    SizedBox(
    width: double.infinity,
    child: ElevatedButton(
    onPressed: _isProcessing
    ? null
        : () {
    setState(() {
    _isProcessing = true;
    });

    // Simuler un traitement de paiement
    Future.delayed(Duration(seconds: 2), () {
      if (mounted) {
        setState(() {
          _isProcessing = false;
        });

        // Rediriger vers la confirmation de paiement
        context.router.push(const PaymentConfirmationRoute());
      }
    });
    },
      style: ElevatedButton.styleFrom(
        backgroundColor: AppTheme.primaryColor,
        padding: EdgeInsets.symmetric(vertical: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
      child: _isProcessing
          ? SizedBox(
        height: 20,
        width: 20,
        child: CircularProgressIndicator(
          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
          strokeWidth: 2,
        ),
      )
          : Text(
        'Procéder au paiement',
        style: TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.bold,
        ),
      ),
    ),
    ),
              SizedBox(height: 24),
            ],
        ),
      ),
    );
  }

  Widget _buildDurationOption(
      int months,
      String label,
      double totalPrice,
      int discountPercent,
      ) {
    final isSelected = _selectedDuration == months;
    final discountedPrice = totalPrice * (1 - discountPercent / 100);

    return GestureDetector(
      onTap: () {
        setState(() {
          _selectedDuration = months;
        });
      },
      child: Container(
        padding: EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.primaryColor.withOpacity(0.1) : Colors.white,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: isSelected ? AppTheme.primaryColor : Colors.grey.shade300,
            width: isSelected ? 2 : 1,
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              label,
              style: TextStyle(
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                color: isSelected ? AppTheme.primaryColor : null,
              ),
            ),
            if (discountPercent > 0)
              Text(
                '-$discountPercent%',
                style: TextStyle(
                  color: Colors.green,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              ),
            SizedBox(height: 4),
            Text(
              '${discountedPrice.toStringAsFixed(2)}€',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: isSelected ? AppTheme.primaryColor : null,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPaymentMethodSelector(String value, String label, IconData icon) {
    final isSelected = _selectedPaymentMethod == value;

    return GestureDetector(
      onTap: () {
        setState(() {
          _selectedPaymentMethod = value;
        });
      },
      child: Container(
        padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.primaryColor.withOpacity(0.1) : Colors.white,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: isSelected ? AppTheme.primaryColor : Colors.grey.shade300,
            width: isSelected ? 2 : 1,
          ),
        ),
        child: Row(
          children: [
            Icon(
              icon,
              color: isSelected ? AppTheme.primaryColor : Colors.grey,
            ),
            SizedBox(width: 16),
            Text(
              label,
              style: TextStyle(
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                color: isSelected ? AppTheme.primaryColor : null,
              ),
            ),
            Spacer(),
            if (isSelected)
              Icon(
                Icons.check_circle,
                color: AppTheme.primaryColor,
              ),
          ],
        ),
      ),
    );
  }
}

extension StringExtension on String {
  String capitalize() {
    return "${this[0].toUpperCase()}${this.substring(1)}";
  }
}