# code/db.py
import os
from typing import Generator
from sqlmodel import SQLModel, create_engine, Session, select
from .models import Ordinateur

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./supervision.db")
# connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
connect_args = {}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

# CRUD helpers
def add_ordinateur(session: Session, ordinateur):
    session.add(ordinateur)
    session.commit()
    session.refresh(ordinateur)
    return ordinateur

def get_all_ordinateurs(session: Session):
    return session.exec(select(Ordinateur)).all()  # placeholder; use direct query where needed

def reset_db():
    # Supprime toutes les tables existantes
    SQLModel.metadata.drop_all(engine)
    # Puis recrée les tables
    SQLModel.metadata.create_all(engine)

# Supprime le fichier DB si il existe
if os.path.exists("supervision.db"):
    os.remove("supervision.db")
create_db_and_tables()
reset_db()
