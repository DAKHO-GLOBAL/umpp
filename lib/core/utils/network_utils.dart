import 'dart:io';
import 'package:connectivity_plus/connectivity_plus.dart';

class NetworkUtils {
  // Vérifier la connexion Internet
  static Future<bool> hasInternetConnection() async {
    try {
      // Vérifier la connectivité
      final connectivityResult = await Connectivity().checkConnectivity();
      if (connectivityResult == ConnectivityResult.none) {
        return false;
      }

      // Vérifier la connectivité réelle en effectuant une requête
      final result = await InternetAddress.lookup('google.com');
      return result.isNotEmpty && result[0].rawAddress.isNotEmpty;
    } catch (_) {
      return false;
    }
  }

  // Récupérer le type de connexion
  static Future<String> getConnectionType() async {
    final connectivityResult = await Connectivity().checkConnectivity();

    switch (connectivityResult) {
      case ConnectivityResult.mobile:
        return 'Mobile';
      case ConnectivityResult.wifi:
        return 'WiFi';
      case ConnectivityResult.ethernet:
        return 'Ethernet';
      case ConnectivityResult.bluetooth:
        return 'Bluetooth';
      case ConnectivityResult.none:
        return 'Aucune';
      default:
        return 'Inconnue';
    }
  }

  // Vérifier si un serveur est accessible
  static Future<bool> isServerReachable(String url) async {
    try {
      final uri = Uri.parse(url);
      final response = await HttpClient().getUrl(uri)
        ..close();
      return true;
    } catch (_) {
      return false;
    }
  }

  // Observer les changements de connectivité
  static Stream<ConnectivityResult> observeConnectivity() {
    return Connectivity().onConnectivityChanged;
  }
}