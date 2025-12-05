# code/models.py
from enum import Enum
import re
import socket
import os
from typing import Optional, Tuple, Dict, ClassVar
from sqlmodel import SQLModel, Field, Column, String #, Integer, Float
from pydantic import BaseModel, field_validator, model_validator

import paramiko

class ComputerStatus(str, Enum):
    ON = "ON"
    OFF = "OFF"
    RELOADING = "RELOADING"

class SSHConnection(BaseModel):
    hostname: Optional[str] = ""
    username: Optional[str] = ""
    password: Optional[str] = ""
    key_filename: Optional[str] = ""
    port: int = 22

    def execute_command(self, command: str) -> Tuple[str, str, int]:
        """
        Execute a command via paramiko. Returns (stdout, stderr, exit_code).
        If paramiko not configured or error, returns ("", error_message, -1).
        """
        if not self.hostname:
            return "", "No hostname configured", -1
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.hostname, port=self.port,
                           username=self.username or None,
                           password=self.password or None,
                           key_filename=self.key_filename or None,
                           timeout=5)  # small timeout for tests
            _, stdout, stderr = client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode(errors="ignore")
            err = stderr.read().decode(errors="ignore")
            client.close()
            return out, err, exit_code
        except Exception as e:
            return "", str(e), -1

class OrdinateurBase(BaseModel):
    mac: str
    ip: str
    hostname: str = ""
    taille_disque: int
    os: str
    status: ComputerStatus
    ram: float = 0.0
    joignable: bool = False
    ssh_conn: ClassVar[Optional[SSHConnection]] = None

    @field_validator("mac")
    def validate_mac(cls, v: str) -> str:
        mac_pattern = r'^([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2})$'
        if not re.match(mac_pattern, v):
            raise ValueError("Invalid MAC address format.")
        return v.upper()

    @field_validator("ip")
    def validate_ip(cls, v: str) -> str:
        ip_pattern = (
            r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
            r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        )
        if not re.match(ip_pattern, v):
            raise ValueError("Invalid IP address format.")
        return v

    @model_validator(mode="after")
    def autoset_fields(self):
        # hostname auto-resolution
        if not self.hostname:
            try:
                self.hostname = socket.gethostbyaddr(self.ip)[0]
            except Exception:
                self.hostname = ""
        if self.ssh_conn and not self.ssh_conn.hostname:
            self.ssh_conn.hostname = self.ip
        # try to fetch RAM via SSH if available
        if self.ram == 0.0 and self.ssh_conn:
            try:
                stdout, _, exit_code = self.ssh_conn.execute_command("free -m")
                if exit_code == 0:
                    self.ram = float(stdout.strip().split("\n")[1].split()[1]) / 1024
            except Exception:
                self.ram = 0.0
        # ping check (non-blocking-ish)
        if self.joignable is False:
            try:
                ping_target = self.hostname or self.ip
                response = os.system(f"ping -c 1 -W 1 {ping_target} > /dev/null 2>&1")
                self.joignable = (response == 0)
            except Exception:
                self.joignable = False
        return self

class Ordinateur(SQLModel, OrdinateurBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    mac: str = Field(
        sa_column=Column(String(17), unique=True, index=True)  # AA:BB:CC:DD:EE:FF
    )

    ip: str = Field(
        sa_column=Column(String(15), unique=True, index=True)  # 255.255.255.255
    )

    hostname: str = Field(
        default="",
        sa_column=Column(String(255))
    )

    taille_disque: int

    os: str = Field(
        sa_column=Column(String(100))
    )

    status: ComputerStatus = Field(default=ComputerStatus.OFF)
    ram: float = Field(default=0.0)
    joignable: bool = Field(default=False)
    # We store SSH connection as JSON via pydantic; not persisted by SQLModel as a column here.
    # For simple persistence, we won't persist ssh_conn into DB in this minimal example.

    # ========== Instance helper methods (same as before) ==========
    def get_free_memory(self) -> float:
        if self.ssh_conn:
            stdout, _, exit_code = self.ssh_conn.execute_command("free -m")
            if exit_code == 0:
                return float(stdout.strip().split("\n")[1].split()[3]) / 1024
        else:
            try:
                cmd_output = os.popen("free -m").readlines()
                return float(cmd_output[1].split()[3]) / 1024
            except Exception:
                return 0.0
        return 0.0

    def get_max_memory(self) -> float:
        if self.ssh_conn:
            stdout, _, exit_code = self.ssh_conn.execute_command("free -m")
            if exit_code == 0:
                return float(stdout.strip().split("\n")[1].split()[1]) / 1024
        else:
            try:
                cmd_output = os.popen("free -m").readlines()
                return float(cmd_output[1].split()[1]) / 1024
            except Exception:
                return 0.0
        return 0.0

    def get_cpu_load(self) -> float:
        if self.ssh_conn:
            stdout, _, exit_code = self.ssh_conn.execute_command("top -bn1 | grep 'Cpu(s)'")
            if exit_code == 0:
                match = re.findall(r'(\d+\.\d+)\s*id', stdout)
                if match:
                    cpu_idle = float(match[0])
                    return 100.0 - cpu_idle
        else:
            try:
                cmd_output = os.popen("top -bn1 | grep 'Cpu(s)'").readline()
                match = re.findall(r'(\d+\.\d+)\s*id', cmd_output)
                if match:
                    cpu_idle = float(match[0])
                    return 100.0 - cpu_idle
            except Exception:
                return 0.0
        return 0.0

    def get_os_release(self) -> Dict:
        if not getattr(self, "ssh_conn", None):
            return {"success": False, "error": "SSH credentials not configured"}
        if self.ssh_conn is None:
            raise RuntimeError("SSH connection not initialized")

        stdout, stderr, exit_code = self.ssh_conn.execute_command("cat /etc/os-release")
        if exit_code != 0:
            return {"success": False, "error": stderr}
        os_info = {}
        for line in stdout.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                os_info[key] = value.strip('"')
        return {"success": True, "os_release": os_info}
