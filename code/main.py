from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator, model_validator
from enum import Enum
import re
import json, os
import socket
import paramiko
from typing import Optional

from sqlmodel import Field, SQLModel, create_engine, Session, select, column, Integer, String, Float




class Ordi(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    mac: str
    ip : str
    hostname : str
    taille_disque: float
    os : str
    status: str
    ram: float
    joignable : bool = False
    ssh_conn: str = ""


sqlite_file_name = "supervision.db"

sqlite_url = f"sqlite:///{sqlite_file_name}"

# sqlite_url = "mariadb:///root:bonjour@localhost/ordinateurs"
# sqlite_url = "mysql+pymysql://root:bonjour@localhost:3306/ordinateurs"

engine = create_engine(sqlite_url, echo=True, pool_pre_ping=True)

SQLModel.metadata.create_all(engine)

session = Session(engine)


class ComputerStatus(str, Enum):
    ON = 1
    OFF = 0
    RELOADING = 2

app = FastAPI()


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

        if self.joignable == False:
            try:
                ping_target = self.hostname if self.hostname else self.ip
                response = os.system(f"ping -c 1 -W 1 {ping_target} > /dev/null 2>&1")
                self.joignable = (response == 0)
            except Exception:
                self.joignable = False

        return self

    def get_free_memory(self) -> float:
        if self.ssh_conn:
            ssh =  self.ssh_conn
            stdout, stderr, exit_code = ssh.execute_command("free -m")
            if exit_code == 0:
                return float(stdout.strip().split('\n')[1].split()[3]) / 1024
        else:
            cmd_output = os.popen("free -m").readlines()
            return float(cmd_output[1].split()[3]) / 1024
        return 0.0
    def get_max_memory(self) -> float:
        if self.ssh_conn:
            ssh =  self.ssh_conn
            stdout, stderr, exit_code = ssh.execute_command("free -m")
            if exit_code == 0:
                return float(stdout.strip().split('\n')[1].split()[1]) / 1024
        else:
            cmd_output = os.popen("free -m").readlines()
            return float(cmd_output[1].split()[1]) / 1024
        return 0.0
    
    
    def get_cpu_load(self) -> float:
        if self.ssh_conn:
            ssh =  self.ssh_conn
            stdout, stderr, exit_code = ssh.execute_command("top -bn1 | grep 'Cpu(s)'")
            if exit_code == 0:
                cpu_idle = float(re.findall(r'(\d+\.\d+)\s*id', stdout)[0])
                return 100.0 - cpu_idle
        else:
            cmd_output = os.popen("top -bn1 | grep 'Cpu(s)'").readline()
            cpu_idle = float(re.findall(r'(\d+\.\d+)\s*id', cmd_output)[0])
            return 100.0 - cpu_idle
        return 0.0


    def get_os_release(self) -> dict:
        if not self.ssh_conn:
            return {"success": False, "error": "SSH credentials not configured"}

        ssh =  self.ssh_conn
        stdout, stderr, exit_code = ssh.execute_command("cat /etc/os-release")

        if exit_code != 0:
            return {"success": False, "error": stderr}

        os_info = {}
        for line in stdout.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                os_info[key] = value.strip('"')

        return {"success": True, "os_release": os_info}


ordi = Ordi(hostname="azz", mac="00:1B:44:11:3A:B7", ip="192.168.1.1", taille_disque=512, os="Windows 10", status=ComputerStatus.ON, ram=16.0)
session.add(ordi)
session.add(Ordi(hostname="a", mac="00:1B:44:11:3A:B8", ip="192.168.1.2", taille_disque=256, os="Ubuntu 20.04", status=ComputerStatus.OFF, ram=8.0))
session.commit()

# ordinateurs = []
# ordinateurs.append(Ordinateur(mac="00:1B:44:11:3A:B7", ip="192.168.1.1", taille_disque=512, os="Windows 10", status=ComputerStatus.ON, ram=16.0))
# ordinateurs.append(Ordinateur(mac="00:1B:44:11:3A:B8", ip="192.168.1.2", taille_disque=256, os="Ubuntu 20.04", status=ComputerStatus.OFF, ram=8.0))

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API FastAPI"}

@app.get("/ordinateurs")
def get_ordinateurs():
    return session.query(Ordi).all()

# @app.get("/save_ordinateurs")
# def save_ordinateurs():
#     with open("ordinateurs.json", "w+") as f:
#         json.dump([ordinateur.model_dump() for ordinateur in ordinateurs], f)
#         return {"message": "Ordinateurs saved to ordinateurs.json"}
    
@app.post("/add_ordinateur")
def post_ordinateur(ordinateur: Ordinateur):
    ordi = Ordinateur.model_dump(ordinateur)
    session.add(ordi)
    session.commit()
    return {"message": "Ordinateur added successfully"}

@app.put("/edit_ordinateur")
def put_ordinateur(ordinateur: Ordinateur):
    ordi = session.exec(select(Ordi).where(Ordi.ip == ordinateur.ip)).first()
    if ordi:
        for key, value in ordinateur.model_dump().items():
            setattr(ordi, key, value)
        session.commit()
        return {"message": "Ordinateur added successfully"}
    return HTTPException(status_code=404, detail="Ordinateur not found")    

@app.delete("/delete_ordinateur/{ip}")
def delete_ordinateur(ip: str):
    ordi = session.exec(select(Ordi).where(Ordi.ip == ip)).first()
    if not ordi:
        return HTTPException(status_code=404, detail="Ordinateur not found")
    session.delete(ordi)
    session.commit()
    return {"message": "Ordinateur deleted successfully"}

@app.get("/memory/{ip}")
def free_memory(ip: str):
    ordi = session.exec(select(Ordi).where(Ordi.ip == ip)).first()
    if ordi:
        ordinateur = Ordinateur.model_validate(ordi)
        total_memory = ordinateur.get_max_memory()
        free_memory = ordinateur.get_free_memory()
        return {"free_memory": free_memory, "total_memory": total_memory}
    return HTTPException(status_code=404, detail="Ordinateur not found")

@app.get("/load_ordinateurs")
def load_ordinateurs():
    try:
        with open("ordinateurs.json", "r") as f:
            data = json.load(f)
            ordinateurs = [Ordinateur(**item) for item in data]
            return {"message": "Ordinateurs loaded from ordinateurs.json","ordinateurs": ordinateurs}
    except FileNotFoundError:
        return HTTPException(status_code=404, detail="File not found")
    
@app.get("/cpu_load/{ip}")
def cpu_load(ip: str):
    ordi = session.exec(select(Ordi).where(Ordi.ip == ip)).first()
    if ordi:
        ordinateur = Ordinateur.model_validate(ordi)
        cpu_load = ordinateur.get_cpu_load()
        return {"cpu_load": cpu_load}
    return HTTPException(status_code=404, detail="Ordinateur not found")

@app.get("/os_release/{ip}")
def os_release(ip: str):
    ordi = session.exec(select(Ordi).where(Ordi.ip == ip)).first()
    if ordi:
        ordinateur = Ordinateur.model_validate(ordi)
        return ordinateur.get_os_release()
    raise HTTPException(status_code=404, detail="Ordinateur not found")

