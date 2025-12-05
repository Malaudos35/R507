

@model_validator(mode="after")
def autoset_fields(self):
    # si ssh_conn_json est un dict, le convertir en SSHConnection
    if isinstance(self.ssh_conn_json, dict):
        self.ssh_conn = SSHConnection(**self.ssh_conn_json)

    # hostname auto-resolution
    if not self.hostname:
        try:
            self.hostname = socket.gethostbyaddr(self.ip)[0]
        except Exception:
            self.hostname = ""

    # si ssh_conn existe et n'a pas de hostname, on met l'IP
    if self.ssh_conn and isinstance(self.ssh_conn, SSHConnection):
        if not self.ssh_conn.hostname:
            self.ssh_conn.hostname = self.ip

    # try to fetch RAM via SSH if available
    if self.ram == 0.0 and isinstance(self.ssh_conn, SSHConnection):
        try:
            stdout, _, exit_code = self.ssh_conn.execute_command("free -m")
            if exit_code == 0:
                self.ram = float(stdout.strip().split("\n")[1].split()[1]) / 1024
        except Exception:
            self.ram = 0.0

    # ping check
    if self.joignable is False:
        try:
            ping_target = self.hostname or self.ip
            response = os.system(f"ping -c 1 -W 1 {ping_target} > /dev/null 2>&1")
            self.joignable = (response == 0)
        except Exception:
            self.joignable = False

    return self
