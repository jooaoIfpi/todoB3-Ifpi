from fastapi.testclient import TestClient
from src.todob3_dev.controllers import app


client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200