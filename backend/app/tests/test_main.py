from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to NCRTC Bus Management System API"}

def test_auth_docs_exists():
    response = client.get("/docs")
    assert response.status_code == 200
