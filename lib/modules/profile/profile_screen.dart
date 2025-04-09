import 'package:flutter/material.dart';
import 'package:auto_route/auto_route.dart';
import 'package:provider/provider.dart';
import 'package:smart_turf/data/providers/auth_provider.dart';
import 'package:smart_turf/routes/app_router.dart';
import 'package:smart_turf/theme/app_theme.dart';

@RoutePage()
class ProfileScreen extends StatelessWidget {
  const ProfileScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);
    final user = authProvider.currentUser;

    return Scaffold(
      appBar: AppBar(
        title: Text('Mon profil'),
        backgroundColor: AppTheme.primaryColor,
        actions: [
          IconButton(
            icon: Icon(Icons.exit_to_app),
            onPressed: () async {
              await authProvider.logout();
              if (context.mounted) {
                context.router.replace(const LoginRoute());
              }
            },
            tooltip: 'Déconnexion',
          ),
        ],
      ),
      body: user == null
          ? Center(child: CircularProgressIndicator())
          : Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Avatar et informations de base
            Row(
              children: [
                CircleAvatar(
                  radius: 40,
                  backgroundColor: AppTheme.primaryColorLight,
                  backgroundImage: user.profilePicture != null
                      ? NetworkImage(user.profilePicture!)
                      : null,
                  child: user.profilePicture == null
                      ? Text(
                    user.username.substring(0, 1).toUpperCase(),
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  )
                      : null,
                ),
                SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        user.fullName,
                        style: Theme.of(context)
                            .textTheme
                            .titleLarge
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      SizedBox(height: 4),
                      Text(
                        '@${user.username}',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                      SizedBox(height: 4),
                      Text(
                        user.email,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: AppTheme.textSecondaryColor,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            SizedBox(height: 24),

            // Menu des options du profil
            Expanded(
              child: ListView(
                children: [
                  ListTile(
                    leading: Icon(Icons.person_outline),
                    title: Text('Modifier mon profil'),
                    trailing: Icon(Icons.chevron_right),
                    onTap: () {
                      // Navigation vers l'édition du profil
                    },
                  ),
                  ListTile(
                    leading: Icon(Icons.vpn_key_outlined),
                    title: Text('Changer de mot de passe'),
                    trailing: Icon(Icons.chevron_right),
                    onTap: () {
                      // Navigation vers le changement de mot de passe
                    },
                  ),
                  ListTile(
                    leading: Icon(Icons.credit_card_outlined),
                    title: Text('Mon abonnement'),
                    subtitle: Text('${user.subscriptionLevel} - Valide jusqu\'au ${user.subscriptionExpiry?.toString().substring(0, 10) ?? 'N/A'}'),
                    trailing: Icon(Icons.chevron_right),
                    onTap: () {
                      context.router.push(const SubscriptionsRoute());
                    },
                  ),
                  Divider(),
                  ListTile(
                    leading: Icon(Icons.history),
                    title: Text('Historique des prédictions'),
                    trailing: Icon(Icons.chevron_right),
                    onTap: () {
                      // Navigation vers l'historique des prédictions
                    },
                  ),
                  ListTile(
                    leading: Icon(Icons.settings_outlined),
                    title: Text('Paramètres'),
                    trailing: Icon(Icons.chevron_right),
                    onTap: () {
                      // Navigation vers les paramètres
                    },
                  ),
                  Divider(),
                  ListTile(
                    leading: Icon(Icons.help_outline),
                    title: Text('Aide et support'),
                    trailing: Icon(Icons.chevron_right),
                    onTap: () {
                      // Navigation vers l'aide
                    },
                  ),
                  ListTile(
                    leading: Icon(Icons.privacy_tip_outlined),
                    title: Text('Politique de confidentialité'),
                    trailing: Icon(Icons.chevron_right),
                    onTap: () {
                      // Navigation vers la politique de confidentialité
                    },
                  ),
                  ListTile(
                    leading: Icon(Icons.exit_to_app, color: Colors.red),
                    title: Text(
                      'Déconnexion',
                      style: TextStyle(color: Colors.red),
                    ),
                    onTap: () async {
                      await authProvider.logout();
                      if (context.mounted) {
                        context.router.replace(const LoginRoute());
                      }
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
}