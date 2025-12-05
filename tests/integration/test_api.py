import httpx

BASE_URL = "http://localhost:8000"


def test_root():
    r = httpx.get(f"{BASE_URL}/")
    assert r.status_code == 200
    assert r.json() == {"message": "Bienvenue sur l'API FastAPI"}

def test_clean():
    r = httpx.get(f"{BASE_URL}/clean")
    assert r.status_code == 200

def test_add_ordinateur():
    data = {
        "mac": "AA:BB:CC:DD:EE:94",
        "ip": "192.168.1.250",
        "taille_disque": 512,
        "os": "Ubuntu 22.04",
        "status": "ON",
        "ram": 16.0
    }

    r = httpx.post(f"{BASE_URL}/add_ordinateur", json=data)
    assert r.status_code == 200
    body = r.json()
    # assert body["ip"] == data["ip"]
    # assert body["mac"] == data["mac"]
    
def test_add_ordinateur2():
    data = {
        "mac": "AA:BB:CC:DD:EE:92",
        "ip": "192.168.1.252",
        "taille_disque": 512,
        "os": "Ubuntu 22.04",
        "status": "ON",
        "ram": 16.0
    }

    r = httpx.post(f"{BASE_URL}/add_ordinateur", json=data)
    assert r.status_code == 200
    body = r.json()
    # assert body["ip"] == data["ip"]
    # assert body["mac"] == data["mac"]
    
def test_add_ordinateur_with_ssh():
    data = {
        "mac": "AA:BB:CC:DD:EE:93",
        "ip": "192.168.1.253",
        "taille_disque": 512,
        "os": "Ubuntu 22.04",
        "status": "ON",
        "ram": 16.0,
        "ssh_conn": {
            "hostname": "192.168.1.253",
            "username": "user",
            "password": "bonjour",
            "port": 22
        }
    }

    r = httpx.post(f"{BASE_URL}/add_ordinateur", json=data)
    assert r.status_code == 200
    # body = r.json()
    # assert body["ip"] == data["ip"]
    # assert body["mac"] == data["mac"]

    # Vérifie la récupération OS via SSH
    # r2 = httpx.get(f"{BASE_URL}/os_release/192.168.1.250")
    # assert r2.status_code == 200
    # result = r2.json()
    # assert "success" in result
    # assert result["success"] is True or result["success"] is False  # selon disponibilité SSH


def test_get_ordinateurs():
    r = httpx.get(f"{BASE_URL}/ordinateurs")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 0


def test_edit_ordinateur():
    updated = {
        "mac": "AA:BB:CC:DD:EE:91",
        "ip": "192.168.1.250",
        "taille_disque": 1024,
        "os": "Windows 11",
        "status": "ON",
        "ram": 32.0
    }

    r = httpx.put(f"{BASE_URL}/edit_ordinateur", json=updated)
    assert r.status_code == 200
    assert r.json()["message"] == "Ordinateur updated successfully"


def test_memory():
    r = httpx.get(f"{BASE_URL}/memory/192.168.1.253")
    assert r.status_code == 200
    assert "free_memory" in r.json()
    assert "total_memory" in r.json()


def test_cpu():
    r = httpx.get(f"{BASE_URL}/cpu_load/192.168.1.253")
    assert r.status_code == 200
    assert "cpu_load" in r.json()


def test_delete_ordinateur():
    r = httpx.delete(f"{BASE_URL}/delete_ordinateur/192.168.1.250")
    assert r.status_code == 200
    assert r.json()["message"] == "Ordinateur deleted successfully"
