from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_dashboard_loads():
    response = client.get('/')
    assert response.status_code == 200
    assert 'AI VisionGuard' in response.text


def test_system_status_endpoint():
    response = client.get('/api/system-status')
    assert response.status_code == 200
    body = response.json()
    assert 'status' in body
    assert 'people_count' in body


def test_incident_trigger():
    payload = {
        'incident_type': 'unsafe_activity',
        'severity': 'HIGH',
        'confidence': 0.8,
        'details': 'Test manual trigger',
        'people_count': 2,
        'face_count': 2,
    }
    response = client.post('/api/trigger-incident', json=payload)
    assert response.status_code == 200
    assert response.json()['status'] == 'created'
