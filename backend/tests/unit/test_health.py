from campus.api.main import app
from fastapi.testclient import TestClient


def test_health_is_public_and_contains_no_private_data():
    response = TestClient(app).get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
