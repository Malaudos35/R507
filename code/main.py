# code/main.py

from typing import List
from fastapi import FastAPI, HTTPException #, Depends
from sqlmodel import Session, select, delete

from contextlib import asynccontextmanager

from .models import Ordinateur, OrdinateurBase, SSHConnection, ComputerStatus
from .db import engine, create_db_and_tables #, get_session
# from .database import init_db

# session = init_db()

# app = FastAPI()
# cache (compatibilité avec les tests existants)
# app.state.ordinateurs = []

# @app.on_event("startup")
# def on_startup():
#     create_db_and_tables()
#     # load cache from DB (optional)
#     with Session(engine) as session:
#         ords = session.exec(select(Ordinateur)).all()
#         app.state.ordinateurs[:] = ords


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    # ⚡ Crée la liste vide d'abord
    app.state.ordinateurs = []
    # charger depuis DB si nécessaire
    with Session(engine) as session:
        ords = session.exec(select(Ordinateur)).all()
        app.state.ordinateurs[:] = ords
    yield


app = FastAPI(lifespan=lifespan)
app.state.ordinateurs = []

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API FastAPI"}

@app.get("/clean")
def clean():
    try:
        with Session(engine) as session:
            session.exec(delete(Ordinateur))
            session.commit()
        return {"message": "Base nettoyée"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ordinateurs", response_model=List[Ordinateur])
def get_ordinateurs():
    with Session(engine) as session:
        existing = session.exec(
            select(Ordinateur)
        ).all()
        
        if existing:
            return existing


@app.post("/add_ordinateur")
def add_ordinateur(payload: dict):
    # Convert SSH dict en JSON compatible SQLModel
    ssh_data = payload.pop("ssh_conn", None)
    if ssh_data:
        payload["ssh_conn_json"] = ssh_data

    ordinateur = Ordinateur(**payload)

    with Session(engine) as session:
        session.add(ordinateur)
        session.commit()
        session.refresh(ordinateur)
    
    return {"success": True, "id": ordinateur.id}

@app.put("/edit_ordinateur")
def put_ordinateur(ordinateur: Ordinateur):
    try:
        with Session(engine) as session:
            # Vérifier si l'ordinateur existe dans la DB
            stmt = select(Ordinateur).where(Ordinateur.ip == ordinateur.ip)
            existing = session.exec(stmt).first()
            if not existing:
                raise HTTPException(status_code=404, detail="Ordinateur not found in DB")

            # Mettre à jour les champs (sauf id)
            for k, v in ordinateur.model_dump().items():
                if k == "id":
                    continue
                setattr(existing, k, v)

            session.add(existing)
            session.commit()
            session.refresh(existing)

        # Mettre à jour le cache si présent
        cache_updated = False
        for i, o in enumerate(app.state.ordinateurs):
            if o.ip == ordinateur.ip:
                app.state.ordinateurs[i] = existing
                cache_updated = True
                break

        if not cache_updated:
            app.state.ordinateurs.append(existing)

        return {"message": "Ordinateur updated successfully"}

    except HTTPException:
        # On relance les HTTPException
        raise
    except Exception as e:
        # Gestion des erreurs inattendues
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour: {str(e)}") from e

@app.delete("/delete_ordinateur/{ip}")
def delete_ordinateur(ip: str):
    with Session(engine) as session:
        stmt = select(Ordinateur).where(Ordinateur.ip == ip)
        existing = session.exec(stmt).first()
        if existing:
            session.delete(existing)
            session.commit()
    # update cache:
    app.state.ordinateurs[:] = [o for o in app.state.ordinateurs if o.ip != ip]
    return {"message": "Ordinateur deleted successfully"}

@app.post("/ssh/{ip}")
def setup_ssh(ip: str, ssh: SSHConnection):
    for ordinateur in app.state.ordinateurs:
        if ordinateur.ip == ip:
            ordinateur.ssh_conn = ssh
            return {"message": "SSH configuré avec succès"}

    raise HTTPException(status_code=404, detail="Ordinateur not found")

@app.get("/memory/{ip}")
def free_memory(ip: str):
    with Session(engine) as session:
        stmt = select(Ordinateur).where(Ordinateur.ip == ip)
        ordinateur = session.exec(stmt).first()
        if ordinateur:
            
            # forcer le rebuild de SSHConnection
            ssh_conn = ordinateur.ssh_conn
            if not ssh_conn:
                raise HTTPException(status_code=400, detail="SSH not configured")
            return {
                "free_memory": ordinateur.get_free_memory(),
                "total_memory": ordinateur.get_max_memory()
            }
    raise HTTPException(status_code=404, detail="Ordinateur not found")

@app.get("/cpu_load/{ip}")
def cpu_load(ip: str):
    with Session(engine) as session:
        stmt = select(Ordinateur).where(Ordinateur.ip == ip)
        ordinateur = session.exec(stmt).first()
        if ordinateur:
            if not ordinateur.ssh_conn:
                raise HTTPException(status_code=400, detail="SSH not configured")
            return {"cpu_load": ordinateur.get_cpu_load()}
    raise HTTPException(status_code=404, detail="Ordinateur not found")

@app.get("/os_release/{ip}")
def os_release(ip: str):
    with Session(engine) as session:
        stmt = select(Ordinateur).where(Ordinateur.ip == ip)
        ordinateur = session.exec(stmt).first()
        if ordinateur:
            if not ordinateur.ssh_conn:
                raise HTTPException(status_code=400, detail="SSH not configured")
            return ordinateur.get_os_release()
    raise HTTPException(status_code=404, detail="Ordinateur not found")
