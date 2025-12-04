FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml poetry.lock /app/
RUN pip install "poetry>=1.5"
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

COPY . /app

EXPOSE 8000

CMD ["uvicorn", "code.main:app", "--host", "0.0.0.0", "--port", "8000"]
