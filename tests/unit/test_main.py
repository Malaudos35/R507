# tests/unit/test_main.py
from code.main import app
from code.models import Ordinateur, ComputerStatus

import unittest
from fastapi.testclient import TestClient


if not hasattr(app.state, "ordinateurs"):
    app.state.ordinateurs = []

class TestMain(unittest.TestCase):

    def setUp(self):
        app.state.ordinateurs.clear()
        app.state.ordinateurs.append(Ordinateur(
            mac="00:1B:44:11:3A:B7",
            ip="192.168.1.1",
            taille_disque=512,
            os="Windows 10",
            status=ComputerStatus.ON,
            ram=16.0
        ))

    def test_read_root(self):
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Bienvenue sur l'API FastAPI"}

    def test_get_ordinateurs(self):
        client = TestClient(app)
        response = client.get("/ordinateurs")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_add_ordinateur(self):
        client = TestClient(app)
        new_ordinateur = {
            "mac": "00:1B:44:11:3A:B9",
            "ip": "192.168.1.3",
            "taille_disque": 1024,
            "os": "Ubuntu 22.04",
            "status": "ON",
            "ram": 32.0
        }
        r = client.post("/add_ordinateur", json=new_ordinateur)
        assert r.status_code == 200

    def test_edit_ordinateur(self):
        client = TestClient(app)
        updated_ordinateur = {
            "mac": "00:1B:44:11:3A:B7",
            "ip": "192.168.1.3",
            "taille_disque": 1024,
            "os": "Windows 11",
            "status": "ON",
            "ram": 32.0
        }
        r = client.put("/edit_ordinateur", json=updated_ordinateur)
        assert r.status_code == 200

    def test_delete_ordinateur(self):
        client = TestClient(app)
        r = client.delete("/delete_ordinateur/192.168.1.1")
        assert r.status_code == 200
        assert len(app.state.ordinateurs) == 0
