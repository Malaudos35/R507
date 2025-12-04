from code.main import app
from code.models import Ordinateur, ComputerStatus
from code.db import get_session

import pytest
from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient



# Engine SQLite en mémoire
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

@pytest.fixture(scope="function")
def session():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def client(session):
    # Remplace le moteur de la DB pour les tests
    # from code.db import get_session
    def get_test_session():
        return session
    app.dependency_overrides[get_session] = get_test_session
    return TestClient(app)

@pytest.fixture(scope="function")
def sample_ordinateur(session):
    ordinateur = Ordinateur(
        mac="00:1B:44:11:3A:B7",
        ip="192.168.1.1",
        hostname="",
        taille_disque=512,
        os="Windows 10",
        status=ComputerStatus.ON,
        ram=16.0,
        joignable=True
    )
    session.add(ordinateur)
    session.commit()
    session.refresh(ordinateur)
    return ordinateur
