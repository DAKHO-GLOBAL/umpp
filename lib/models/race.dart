class Race {
  final int id;
  final DateTime dateHeure;
  final String? lieu;
  final String? typeCourse;
  final int? distance;
  final String? terrain;
  final int? numCourse;
  final String? libelle;
  final String? corde;
  final String? discipline;
  final String? specialite;

  Race({
    required this.id,
    required this.dateHeure,
    this.lieu,
    this.typeCourse,
    this.distance,
    this.terrain,
    this.numCourse,
    this.libelle,
    this.corde,
    this.discipline,
    this.specialite,
  });

  factory Race.fromJson(Map<String, dynamic> json) {
    return Race(
      id: json['id'],
      dateHeure: DateTime.parse(json['date_heure']),
      lieu: json['lieu'],
      typeCourse: json['type_course'],
      distance: json['distance'],
      terrain: json['terrain'],
      numCourse: json['num_course'],
      libelle: json['libelle'],
      corde: json['corde'],
      discipline: json['discipline'],
      specialite: json['specialite'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'date_heure': dateHeure.toIso8601String(),
      'lieu': lieu,
      'type_course': typeCourse,
      'distance': distance,
      'terrain': terrain,
      'num_course': numCourse,
      'libelle': libelle,
      'corde': corde,
      'discipline': discipline,
      'specialite': specialite,
    };
  }
}