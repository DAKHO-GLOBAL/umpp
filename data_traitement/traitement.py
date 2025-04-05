from datetime import datetime
from database.database import save_pays, save_hippodrome, save_reunions, save_courses, save_participation,save_course

def save_race_data(reunion_data):
    """Traite et sauvegarde les données de réunion/courses"""
    courses_saved = []
    
    # Extraire les informations essentielles
    for course_data in reunion_data.get('courses', []):
        # Convertir le timestamp en datetime
        heure_depart = datetime.fromtimestamp(course_data['heureDepart'] / 1000.0)
        
        # Créer un dictionnaire avec les données de la course
        course = {
            'date_heure': heure_depart,
            'lieu': course_data.get('hippodrome', {}).get('libelleLong'),
            'type_course': course_data.get('specialite'),
            'distance': course_data.get('distance'),
            'terrain': '',  # Non disponible directement, pourrait être ajouté plus tard
            'num_course': course_data.get('numOrdre'),
            'libelle': course_data.get('libelle'),
            'discipline': course_data.get('discipline'),
            'specialite': course_data.get('specialite'),
            'corde': course_data.get('corde'),
            'nombre_partants': course_data.get('nombreDeclaresPartants'),
            'ordreArrivee': course_data.get('ordreArrivee')
        }
        
        # Sauvegarder la course et récupérer son ID
        course_id = save_course(course)
        
        # Ajouter des informations pour le suivi
        courses_saved.append({
            'id': course_id,
            'num_reunion': course_data.get('numReunion'),
            'num_course': course_data.get('numOrdre')
        })
    
    return courses_saved

def save_participants_data(participants_data, course_id):
    """Traite et sauvegarde les données des participants"""
    for participant in participants_data.get('participants', []):
        # Extraire les informations du cheval
        cheval_data = {
            'nom': participant.get('nom'),
            'age': participant.get('age'),
            'sexe': participant.get('sexe'),
            'proprietaire': participant.get('proprietaire'),
            'nomPere': participant.get('nomPere'),
            'nomMere': participant.get('nomMere')
        }
        
        # Extraire les informations du jockey
        jockey_data = {
            'nom': participant.get('driver'),
            'pays': ''  # Pas toujours disponible
        }
        
        # Extraire les informations de participation
        participation_data = {
            'id_course': course_id,
            'position': participant.get('ordreArrivee'),
            'poids': participant.get('handicapPoids'),
            'est_forfait': participant.get('statut') == 'NON_PARTANT',
            'statut': participant.get('statut')
        }
        
        # Extraire les cotes
        if 'dernierRapportDirect' in participant and 'rapport' in participant['dernierRapportDirect']:
            participation_data['cote_actuelle'] = participant['dernierRapportDirect']['rapport']
        
        if 'dernierRapportReference' in participant and 'rapport' in participant['dernierRapportReference']:
            participation_data['cote_initiale'] = participant['dernierRapportReference']['rapport']
        
        # Sauvegarder le participant
        save_participation(cheval_data, jockey_data, participation_data)
