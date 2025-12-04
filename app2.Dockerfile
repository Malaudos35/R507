# Utiliser une image de base légère avec Python
FROM python:3.14

RUN pip install poetry

# Copier uniquement les fichiers nécessaires pour l'installation des dépendances
WORKDIR /app
COPY pyproject.toml poetry.lock README.md ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root


# CMD ["poetry", "run", "python", "-m", "src.mon_module"]
CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--reload" ]