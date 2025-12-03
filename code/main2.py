from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, field_validator, model_validator
from enum import Enum
import re
import json
import os
import socket
import paramiko
from typing import Optional, List
from sqlmodel import Field, SQLModel, create_engine, Session, select

# --- Modèle SQLModel pour la base de données ---
class Ordi(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    mac: str
    ip: str
    hostname: str
    taille_disque: float
    os: str
    status: str
    ram: float
    joignable: str
    ssh_conn: str

# --- Configuration de la base de données SQLite ---
sqlite_file_name = "supervision.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# Crée le moteur et les tables
engine = create_engine(sqlite_url, echo=True)
SQLModel.metadata.create_all(engine)

# --- Gestion de la session SQLModel ---
def get_db_session():
    with Session(engine) as session:
        yield session

# --- Modèles Pydantic ---
class ComputerStatus(str, Enum):
    ON = "ON"
    OFF = "OFF"
    RELOADING = "RELOADING"

class SSHConnection(BaseModel):
    hostname: Optional[str] = ""
    username: str
    password: Optional[str] = ""
    key_filename: Optional[str] = ""
    port: int = 22

    def execute_command(self, command: str) -> tuple[str, str, int]:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.hostname, self.port, self.username, self.password, key_filename=self.key_filename) # type: ignore
            stdin, stdout, stderr = client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            result = stdout.read().decode(), stderr.read().decode(), exit_code
            client.close()
            return result
        except Exception as e:
            return "", str(e), -1

class Ordinateur(BaseModel):
    mac: str
    ip: str
    hostname: str = ""
    taille_disque: int
    os: str
    status: ComputerStatus
    ram: float = 0.0
    joignable: bool = False
    ssh_conn: Optional[SSHConnection] = None

    @field_validator('mac')
    def validate_mac(cls, v: str) -> str:
        mac_pattern = r'^([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2})$'
        if not re.match(mac_pattern, v):
            raise ValueError('Invalid MAC address format.')
        return v.upper()

    @field_validator('ip')
    def validate_ip(cls, v: str) -> str:
        ip_pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        if not re.match(ip_pattern, v):
            raise ValueError('Invalid IP address format.')
        return v

    @model_validator(mode='after')
    def autoset_fields(self):
        if not self.hostname:
            try:
                self.hostname = socket.gethostbyaddr(self.ip)[0]
            except socket.herror:
                self.hostname = ""
        if self.ssh_conn and not self.ssh_conn.hostname:
            self.ssh_conn.hostname = self.ip
        if self.ram == 0.0 and self.ssh_conn:
            try:
                ssh_conn = self.ssh_conn
                stdout, stderr, exit_code = ssh_conn.execute_command("free -m")
                if exit_code == 0:
                    self.ram = float(stdout.strip().split('\n')[1].split()[1]) / 1024
            except (IndexError, ValueError):
                self.ram = 0.0
        if not self.joignable:
            try:
                ping_target = self.hostname if self.hostname else self.ip
                response = os.system(f"ping -c 1 -W 1 {ping_target} > /dev/null 2>&1")
                self.joignable = (response == 0)
            except Exception:
                self.joignable = False
        return self

    def get_free_memory(self) -> float:
        if self.ssh_conn:
            ssh = self.ssh_conn
            stdout, stderr, exit_code = ssh.execute_command("free -m")
            if exit_code == 0:
                return float(stdout.strip().split('\n')[1].split()[3]) / 1024
        return 0.0

    def get_max_memory(self) -> float:
        if self.ssh_conn:
            ssh = self.ssh_conn
            stdout, stderr, exit_code = ssh.execute_command("free -m")
            if exit_code == 0:
                return float(stdout.strip().split('\n')[1].split()[1]) / 1024
        return 0.0

    def get_cpu_load(self) -> float:
        if self.ssh_conn:
            ssh = self.ssh_conn
            stdout, stderr, exit_code = ssh.execute_command("top -bn1 | grep 'Cpu(s)'")
            if exit_code == 0:
                cpu_idle = float(re.findall(r'(\d+\.\d+)\s*id', stdout)[0])
                return 100.0 - cpu_idle
        return 0.0

    def get_os_release(self) -> dict:
        if not self.ssh_conn:
            return {"success": False, "error": "SSH credentials not configured"}
        ssh = self.ssh_conn
        stdout, stderr, exit_code = ssh.execute_command("cat /etc/os-release")
        if exit_code != 0:
            return {"success": False, "error": stderr}
        os_info = {}
        for line in stdout.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                os_info[key] = value.strip('"')
        return {"success": True, "os_release": os_info}

# --- Application FastAPI ---
app = FastAPI()

# --- Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API FastAPI"}

@app.get("/ordinateurs")
def get_ordinateurs(db: Session = Depends(get_db_session)):
    return db.exec(select(Ordi)).all()

@app.post("/add_ordinateur")
def post_ordinateur(ordinateur: Ordinateur, db: Session = Depends(get_db_session)):
    ordi = Ordi(
        mac=ordinateur.mac,
        ip=ordinateur.ip,
        hostname=ordinateur.hostname,
        taille_disque=ordinateur.taille_disque,
        os=ordinateur.os,
        status=ordinateur.status.value,
        ram=ordinateur.ram,
        joignable=str(ordinateur.joignable),
        ssh_conn=str(ordinateur.ssh_conn)
    )
    db.add(ordi)
    db.commit()
    db.refresh(ordi)
    return {"message": "Ordinateur ajouté avec succès"}

@app.put("/edit_ordinateur/{ip}")
def put_ordinateur(ip: str, ordinateur: Ordinateur, db: Session = Depends(get_db_session)):
    ordi = db.exec(select(Ordi).where(Ordi.ip == ip)).first()
    if not ordi:
        raise HTTPException(status_code=404, detail="Ordinateur non trouvé")
    for key, value in ordinateur.model_dump().items():
        setattr(ordi, key, value)
    db.commit()
    return {"message": "Ordinateur mis à jour avec succès"}

@app.delete("/delete_ordinateur/{ip}")
def delete_ordinateur(ip: str, db: Session = Depends(get_db_session)):
    ordi = db.exec(select(Ordi).where(Ordi.ip == ip)).first()
    if not ordi:
        raise HTTPException(status_code=404, detail="Ordinateur non trouvé")
    db.delete(ordi)
    db.commit()
    return {"message": "Ordinateur supprimé avec succès"}

@app.get("/memory/{ip}")
def free_memory(ip: str, db: Session = Depends(get_db_session)):
    ordi = db.exec(select(Ordi).where(Ordi.ip == ip)).first()
    if not ordi:
        raise HTTPException(status_code=404, detail="Ordinateur non trouvé")
    ordinateur = Ordinateur.model_validate(ordi)
    total_memory = ordinateur.get_max_memory()
    free_memory = ordinateur.get_free_memory()
    return {"free_memory": free_memory, "total_memory": total_memory}

@app.get("/cpu_load/{ip}")
def cpu_load(ip: str, db: Session = Depends(get_db_session)):
    ordi = db.exec(select(Ordi).where(Ordi.ip == ip)).first()
    if not ordi:
        raise HTTPException(status_code=404, detail="Ordinateur non trouvé")
    ordinateur = Ordinateur.model_validate(ordi)
    cpu_load = ordinateur.get_cpu_load()
    return {"cpu_load": cpu_load}

@app.get("/os_release/{ip}")
def os_release(ip: str, db: Session = Depends(get_db_session)):
    ordi = db.exec(select(Ordi).where(Ordi.ip == ip)).first()
    if not ordi:
        raise HTTPException(status_code=404, detail="Ordinateur non trouvé")
    ordinateur = Ordinateur.model_validate(ordi)
    return ordinateur.get_os_release()
