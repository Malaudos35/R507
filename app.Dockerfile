FROM python:3.14

WORKDIR /app

COPY requirements.txt /app/

RUN pip install -r requirements.txt



CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--reload" ]