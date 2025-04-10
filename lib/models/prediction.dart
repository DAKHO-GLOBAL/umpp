class PredictionHorse {
  final int id;
  final String name;
  final int predictedRank;
  final double top1Probability;
  final double top3Probability;
  final double? currentOdds;
  final double? initialOdds;

  PredictionHorse({
    required this.id,
    required this.name,
    required this.predictedRank,
    required this.top1Probability,
    required this.top3Probability,
    this.currentOdds,
    this.initialOdds,
  });

  factory PredictionHorse.fromJson(Map<String, dynamic> json) {
    return PredictionHorse(
      id: json['id_cheval'],
      name: json['cheval_nom'] ?? 'Inconnu',
      predictedRank: json['predicted_rank'] ?? 0,
      top1Probability: (json['in_top1_prob'] ?? 0).toDouble(),
      top3Probability: (json['in_top3_prob'] ?? 0).toDouble(),
      currentOdds: json['cote_actuelle']?.toDouble(),
      initialOdds: json['cote_initiale']?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id_cheval': id,
      'cheval_nom': name,
      'predicted_rank': predictedRank,
      'in_top1_prob': top1Probability,
      'in_top3_prob': top3Probability,
      'cote_actuelle': currentOdds,
      'cote_initiale': initialOdds,
    };
  }
}

class Prediction {
  final int courseId;
  final String predictionType;
  final String timestamp;
  final List<PredictionHorse> horses;
  final List<String>? comments;

  Prediction({
    required this.courseId,
    required this.predictionType,
    required this.timestamp,
    required this.horses,
    this.comments,
  });

  factory Prediction.fromJson(Map<String, dynamic> json) {
    List<PredictionHorse> horses = [];
    if (json['data'] != null) {
      horses = (json['data'] as List).map((horse) => PredictionHorse.fromJson(horse)).toList();
    }

    List<String>? comments;
    if (json['comments'] != null) {
      comments = (json['comments'] as List).map((comment) => comment.toString()).toList();
    }

    return Prediction(
      courseId: json['course_id'],
      predictionType: json['prediction_type'] ?? 'standard',
      timestamp: json['timestamp'] ?? DateTime.now().toIso8601String(),
      horses: horses,
      comments: comments,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'course_id': courseId,
      'prediction_type': predictionType,
      'timestamp': timestamp,
      'data': horses.map((horse) => horse.toJson()).toList(),
      'comments': comments,
    };
  }
}