# test_predictions.py
# test_predictions.py
import json
import pytest
from flask import url_for
from unittest.mock import patch

def test_upcoming_races(client, auth_headers):
    """Test de la récupération des courses à venir"""
    response = client.get(
        '/api/predictions/upcoming',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'data' in data

@patch('api.services.prediction_service.PredictionService.predict_course')
def test_standard_prediction(mock_predict, client, auth_headers, test_course):
    """Test de la prédiction standard"""
    # Configurer le mock pour la prédiction
    mock_predict.return_value = {
        'timestamp': '2025-04-08T10:00:00',
        'data': [
            {
                'id_cheval': 1,
                'cheval_nom': 'Cheval Test 1',
                'predicted_rank': 1,
                'in_top1_prob': 0.75,
                'in_top3_prob': 0.95
            },
            {
                'id_cheval': 2,
                'cheval_nom': 'Cheval Test 2',
                'predicted_rank': 2,
                'in_top1_prob': 0.15,
                'in_top3_prob': 0.80
            }
        ]
    }
    
    response = client.get(
        f'/api/predictions/standard/{test_course.id}',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['course_id'] == test_course.id
    assert 'data' in data
    assert len(data['data']) == 2

@patch('api.services.prediction_service.PredictionService.predict_course')
def test_top3_prediction(mock_predict, client, auth_headers, test_course):
    """Test de la prédiction top3"""
    # Configurer le mock pour la prédiction
    mock_predict.return_value = {
        'timestamp': '2025-04-08T10:00:00',
        'data': [
            {
                'id_cheval': 1,
                'cheval_nom': 'Cheval Test 1',
                'predicted_rank': 1,
                'in_top1_prob': 0.75,
                'in_top3_prob': 0.95
            },
            {
                'id_cheval': 2,
                'cheval_nom': 'Cheval Test 2',
                'predicted_rank': 2,
                'in_top1_prob': 0.15,
                'in_top3_prob': 0.80
            },
            {
                'id_cheval': 3,
                'cheval_nom': 'Cheval Test 3',
                'predicted_rank': 3,
                'in_top1_prob': 0.05,
                'in_top3_prob': 0.60
            }
        ]
    }
    
    response = client.get(
        f'/api/predictions/top3/{test_course.id}',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['course_id'] == test_course.id
    assert 'data' in data
    assert len(data['data']) == 3
    assert 'comments' in data

def test_prediction_history(client, auth_headers):
    """Test de l'historique des prédictions"""
    response = client.get(
        '/api/predictions/history',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'data' in data