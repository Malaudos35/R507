# R507 - Computer Management (FastAPI)

R507 is a **REST API** developed with **FastAPI** to manage a fleet of computers. It allows you to **create, read, update, and delete** computers, as well as retrieve their resources (RAM, CPU, OS).

---

## 🚀 Features

- Add a computer with its specifications (MAC, IP, OS, RAM, etc.)
- Update information for an existing computer
- Delete a computer
- List all computers
- Retrieve memory usage, CPU load, and OS information via SSH (if configured)
- API compatible with unit tests and in-memory cache

---

## 🧩 Technologies Used

- **Python 3.12**
- **FastAPI** for the REST API
- **SQLModel** + SQLite for persistence
- **Paramiko** for SSH connections
- **Uvicorn** as the ASGI server
- **Poetry** for dependency management
- **Docker** for containerization

---

## 📦 Docker Installation

**Build the Docker image:**

```bash
docker build -t R507 -f app3.Dockerfile .
```

**Run the container:**

```bash
docker run -d -p 8000:8000 R507
```

**Access the API:**

- Base URL: `http://localhost:8000`
- Interactive Swagger documentation: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`

---

## ⚙️ Local Development (Poetry)

Install dependencies:

```bash
poetry install
```

Run the API locally:

```bash
poetry run uvicorn code.main:app --reload
```

Run unit tests:

```bash
poetry run pytest
```

or via bash:

```bash
alambic.sh           # export db
linter.sh            # show if code is well write
lunch.sh             # lunch docker and api
test_fonctionnels.sh # test fonctionnels of api
test_unitaires.sh    # test unitaires of api
```

---

## 📝 Main Endpoints

| Method | Endpoint                  | Description                     |
|--------|---------------------------|---------------------------------|
| GET    | `/`                       | Welcome message                  |
| GET    | `/ordinateurs`            | List all computers              |
| POST   | `/add_ordinateur`         | Add a computer                   |
| PUT    | `/edit_ordinateur`        | Update an existing computer      |
| DELETE | `/delete_ordinateur/{ip}` | Delete a computer by IP         |
| GET    | `/memory/{ip}`            | Get free and total memory        |
| GET    | `/cpu_load/{ip}`          | Get CPU load                    |
| GET    | `/os_release/{ip}`        | Get OS information via SSH      |

---

## 📂 Project Structure

```txt
r507/
├─ code/
│  ├─ main.py          # FastAPI application
│  ├─ models.py        # Pydantic and SQLModel models
│  ├─ db.py            # Database and session management
├─ tests/
│  ├─ unit/
│  │  ├─ test_main.py  # Unit tests for the API
├─ pyproject.toml      # Poetry dependencies
├─ poetry.lock
├─ README.md
└─ app3.Dockerfile     # Dockerfile for building the image
```

---

## ⚠️ Notes

- The API uses an **in-memory cache** (`app.state.ordinateurs`) to speed up tests.
- Unit tests reset the cache on each startup.
- SSH connections are optional but required to retrieve certain system information.

---

## 🛠️ Author

**Malo** – [126970037+Malaudos35@users.noreply.github.com](mailto:126970037+Malaudos35@users.noreply.github.com)
[https://github.com/Malaudos35/R507](https://github.com/Malaudos35/R507)
