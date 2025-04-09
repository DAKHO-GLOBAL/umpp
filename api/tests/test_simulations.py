# test_simulations.py
# test_simulations.py
import json
import pytest
from flask import url_for
from unittest.mock import patch

@patch('services.simulation_service.SimulationService.simulate_course')
def test_basic_simulation(mock_simulate, client, auth_headers, test_course):
    """Test de la simulation de base"""
    # Configurer le mock pour la simulation
    mock_simulate.return_value = {
        'simulation_id': 1,
        'timestamp': '2025-04-08T10:00:00',
        'data': [
            {
                'id_cheval': 1,
                'cheval_nom': 'Cheval Test 1',
                'predicted_rank': 1,
                'probability': 0.75
            },
            {
                'id_cheval': 2,
                'cheval_nom': 'Cheval Test 2',
                'predicted_rank': 2,
                'probability': 0.15
            }
        ],
        'animation_data': {
            'distance': 2400,
            'type_course': 'Plat',
            'checkpoints': [0, 0.25, 0.5, 0.75, 1.0],
            'horses': [
                {
                    'id': 1,
                    'name': 'Cheval Test 1',
                    'color': '#bc1a5a',
                    'number': 1,
                    'final_rank': 1,
                    'positions': [0.5, 0.3, 0.2, 0.1, 0]
                },
                {
                    'id': 2,
                    'name': 'Cheval Test 2',
                    'color': '#23bc1a',
                    'number': 2,
                    'final_rank': 2,
                    'positions': [0.4, 0.4, 0.3, 0.3, 0.2]
                }
            ]
        }
    }
    
    response = client.post(
        f'/api/simulations/basic/{test_course.id}',
        json={
            'selected_horses': [1, 2],
            'simulation_params': {'iterations': 100}
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['course_id'] == test_course.id
    assert 'data' in data
    assert 'animation_data' in data

@patch('services.simulation_service.SimulationService.simulate_course')
def test_advanced_simulation(mock_simulate, client, auth_headers, test_course):
    """Test de la simulation avancée"""
    # Configurer le mock pour la simulation
    mock_simulate.return_value = {
        'simulation_id': 2,
        'timestamp': '2025-04-08T10:00:00',
        'data': [
            {
                'id_cheval': 1,
                'cheval_nom': 'Cheval Test 1',
                'predicted_rank': 2,
                'probability': 0.45
            },
            {
                'id_cheval': 2,
                'cheval_nom': 'Cheval Test 2',
                'predicted_rank': 1,
                'probability': 0.55
            }
        ],
        'animation_data': {
            'distance': 2400,
            'type_course': 'Plat',
            'checkpoints': [0, 0.25, 0.5, 0.75, 1.0],
            'horses': [
                {
                    'id': 1,
                    'name': 'Cheval Test 1',
                    'color': '#bc1a5a',
                    'number': 1,
                    'final_rank': 2,
                    'positions': [0.5, 0.4, 0.3, 0.3, 0.2]
                },
                {
                    'id': 2,
                    'name': 'Cheval Test 2',
                    'color': '#23bc1a',
                    'number': 2,
                    'final_rank': 1,
                    'positions': [0.4, 0.3, 0.2, 0.1, 0]
                }
            ]
        }
    }
    
    horse_modifications = {
        '2': {
            'forme': 9,
            'poids': 58
        }
    }
    
    weather_conditions = {
        'weather_type': 'Pluie',
        'temperature': 15
    }
    
    response = client.post(
        f'/api/simulations/advanced/{test_course.id}',
        json={
            'selected_horses': [1, 2],
            'horse_modifications': horse_modifications,
            'weather_conditions': weather_conditions
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['course_id'] == test_course.id
    assert 'data' in data
    assert 'animation_data' in data
    assert data['modifications'] == horse_modifications
    assert data['weather'] == weather_conditions

def test_simulation_history(client, auth_headers):
    """Test de l'historique des simulations"""
    response = client.get(
        '/api/simulations/history',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'data' in data