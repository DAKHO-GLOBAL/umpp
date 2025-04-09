import 'package:intl/intl.dart';
import 'package:smart_turf/core/constants/app_constants.dart';

class DateTimeUtils {
  // Formatter une date au format standard
  static String formatDate(DateTime date) {
    return DateFormat(AppConstants.dateFormat).format(date);
  }

  // Formatter une heure au format standard
  static String formatTime(DateTime time) {
    return DateFormat(AppConstants.timeFormat).format(time);
  }

  // Formatter une date et heure au format standard
  static String formatDateTime(DateTime dateTime) {
    return DateFormat(AppConstants.dateTimeFormat).format(dateTime);
  }

  // Obtenir la différence relative (ex: "il y a 5 minutes")
  static String getRelativeTime(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);

    if (difference.inDays > 365) {
      return 'il y a ${(difference.inDays / 365).floor()} an(s)';
    } else if (difference.inDays > 30) {
      return 'il y a ${(difference.inDays / 30).floor()} mois';
    } else if (difference.inDays > 7) {
      return 'il y a ${(difference.inDays / 7).floor()} semaine(s)';
    } else if (difference.inDays > 0) {
      return 'il y a ${difference.inDays} jour(s)';
    } else if (difference.inHours > 0) {
      return 'il y a ${difference.inHours} heure(s)';
    } else if (difference.inMinutes > 0) {
      return 'il y a ${difference.inMinutes} minute(s)';
    } else {
      return 'à l\'instant';
    }
  }

  // Vérifier si deux dates sont le même jour
  static bool isSameDay(DateTime date1, DateTime date2) {
    return date1.year == date2.year &&
        date1.month == date2.month &&
        date1.day == date2.day;
  }

  // Obtenir le début de la journée
  static DateTime startOfDay(DateTime date) {
    return DateTime(date.year, date.month, date.day);
  }

  // Obtenir la fin de la journée
  static DateTime endOfDay(DateTime date) {
    return DateTime(date.year, date.month, date.day, 23, 59, 59, 999);
  }

  // Formatter la durée au format "1h 30min"
  static String formatDuration(Duration duration) {
    final hours = duration.inHours;
    final minutes = duration.inMinutes.remainder(60);

    if (hours > 0) {
      return '${hours}h ${minutes > 0 ? '${minutes}min' : ''}';
    } else {
      return '${minutes}min';
    }
  }

  // Calculer le temps restant avant une date
  static String timeUntil(DateTime date) {
    final now = DateTime.now();
    final difference = date.difference(now);

    if (difference.isNegative) {
      return 'Terminé';
    }

    final days = difference.inDays;
    final hours = difference.inHours.remainder(24);
    final minutes = difference.inMinutes.remainder(60);

    if (days > 0) {
      return '$days jour(s) ${hours}h';
    } else if (hours > 0) {
      return '${hours}h ${minutes}min';
    } else {
      return '${minutes}min';
    }
  }
}