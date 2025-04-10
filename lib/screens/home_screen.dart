import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import 'package:smart_turf/providers/auth_provider.dart';
import 'package:smart_turf/services/api_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService _apiService = ApiService();
  bool _isLoading = false;
  String _errorMessage = '';
  List<dynamic> _upcomingRaces = [];

  @override
  void initState() {
    super.initState();
    _loadUpcomingRaces();
  }

  Future<void> _loadUpcomingRaces() async {
    setState(() {
      _isLoading = true;
      _errorMessage = '';
    });

    try {
      final races = await _apiService.getUpcomingRaces();
      setState(() {
        _upcomingRaces = races;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
        _isLoading = false;
      });
    }
  }

  void _logout() async {
    await Provider.of<AuthProvider>(context, listen: false).logout();
  }

  @override
  Widget build(BuildContext context) {
    final user = Provider.of<AuthProvider>(context).user;

    return Scaffold(
      appBar: AppBar(
        title: const Text('SmartTurf'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadUpcomingRaces,
          ),
          IconButton(
            icon: const Icon(Icons.exit_to_app),
            onPressed: _logout,
          ),
        ],
      ),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // En-tête avec informations utilisateur
          Container(
            color: Colors.grey.shade100,
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Bienvenue ${user?.fullName ?? 'utilisateur'}',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Abonnement: ${user?.subscriptionLevel}',
                  style: TextStyle(
                    color: Colors.grey.shade700,
                  ),
                ),
              ],
            ),
          ),

          const Padding(
            padding: EdgeInsets.all(16.0),
            child: Text(
              'Courses à venir',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),

          // Liste des courses
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _errorMessage.isNotEmpty
                ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(
                    Icons.error_outline,
                    size: 48,
                    color: Colors.red,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Erreur: $_errorMessage',
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: _loadUpcomingRaces,
                    child: const Text('Réessayer'),
                  ),
                ],
              ),
            )
                : _upcomingRaces.isEmpty
                ? const Center(
              child: Text('Aucune course à venir'),
            )
                : RefreshIndicator(
              onRefresh: _loadUpcomingRaces,
              child: ListView.builder(
                itemCount: _upcomingRaces.length,
                itemBuilder: (context, index) {
                  final race = _upcomingRaces[index];
                  final dateTime = DateTime.parse(race['date_heure']);
                  final formattedDate = DateFormat('dd/MM/yyyy').format(dateTime);
                  final formattedTime = DateFormat('HH:mm').format(dateTime);

                  return Card(
                    margin: const EdgeInsets.symmetric(
                      horizontal: 16.0,
                      vertical: 8.0,
                    ),
                    child: ListTile(
                      title: Text(
                        race['lieu'] ?? 'Course sans lieu',
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      subtitle: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const SizedBox(height: 4),
                          Text(race['libelle'] ?? 'Sans titre'),
                          const SizedBox(height: 4),
                          Text('$formattedDate à $formattedTime'),
                          if (race['distance'] != null)
                            Text('Distance: ${race['distance']}m'),
                        ],
                      ),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () {
                        // Naviguer vers la page détaillée de la course
                        // À implémenter plus tard
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text('Détails de la course ${race['id']}'),
                          ),
                        );
                      },
                    ),
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }
}