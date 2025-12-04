# R507 - Gestion d'ordinateurs (API FastAPI)

R507 est une API REST développée avec **FastAPI** pour gérer un parc d'ordinateurs.  
Elle permet de **créer, lire, mettre à jour et supprimer** des ordinateurs, ainsi que de consulter leurs ressources (RAM, CPU, OS).

---

## 🚀 Fonctionnalités

- Ajouter un ordinateur avec ses caractéristiques (MAC, IP, OS, RAM, etc.)
- Modifier les informations d'un ordinateur existant
- Supprimer un ordinateur
- Lister tous les ordinateurs
- Obtenir l'utilisation mémoire, CPU et informations OS via SSH si configuré
- API compatible avec tests unitaires et cache en mémoire

---

## 🧩 Technologies utilisées

- **Python 3.12**
- **FastAPI** pour l'API REST
- **SQLModel** + SQLite pour la persistance
- **Paramiko** pour les connexions SSH
- **Uvicorn** comme serveur ASGI
- **Poetry** pour la gestion des dépendances
- **Docker** pour le conteneur

---

## 📦 Installation avec Docker

**Build de l'image Docker :**

```bash
docker build -t R507 -f app3.Dockerfile .
```

**Lancer le conteneur :**

```bash
docker run -d -p 8000:8000 R507
```

**Accéder à l'API :**

- Base URL : `http://localhost:8000`
- Documentation interactive Swagger : `http://localhost:8000/docs`
- Documentation ReDoc : `http://localhost:8000/redoc`

---

## ⚙️ Développement local (Poetry)

Installer les dépendances :

```bash
poetry install
```

Lancer l'API en local :

```bash
poetry run uvicorn code.main:app --reload
```

Exécuter les tests unitaires :

```bash
poetry run pytest
```

---

## 📝 Endpoints principaux

| Méthode | Endpoint                  | Description                     |
| ------- | ------------------------- | ------------------------------- |
| GET     | `/`                       | Accueil, message de bienvenue   |
| GET     | `/ordinateurs`            | Liste tous les ordinateurs      |
| POST    | `/add_ordinateur`         | Ajouter un ordinateur           |
| PUT     | `/edit_ordinateur`        | Modifier un ordinateur existant |
| DELETE  | `/delete_ordinateur/{ip}` | Supprimer un ordinateur par IP  |
| GET     | `/memory/{ip}`            | Obtenir mémoire libre et totale |
| GET     | `/cpu_load/{ip}`          | Obtenir charge CPU              |
| GET     | `/os_release/{ip}`        | Obtenir informations OS via SSH |

---

## 📂 Structure du projet

```txt
r507/
├─ code/
│  ├─ main.py          # Application FastAPI
│  ├─ models.py        # Modèles Pydantic et SQLModel
│  ├─ db.py            # Gestion DB et session
├─ tests/
│  ├─ unit/
│  │  ├─ test_main.py  # Tests unitaires API
├─ pyproject.toml      # Dépendances Poetry
├─ poetry.lock
├─ README.md
└─ app3.Dockerfile     # Dockerfile pour build image
```

---

## ⚠️ Notes

- L’API utilise une **cache mémoire** (`app.state.ordinateurs`) pour accélérer les tests.
- Les tests unitaires réinitialisent le cache à chaque démarrage.
- Les connexions SSH sont optionnelles, mais nécessaires pour récupérer certaines infos système.

---

## 🛠️ Auteur

**Malo** – [126970037+Malaudos35@users.noreply.github.com](mailto:126970037+Malaudos35@users.noreply.github.com)

[https://github.com/Malaudos35/R507](https://github.com/Malaudos35/R507)
