#!/bin/bash

clear

docker compose down

docker compose up --build

# clear && uvicorn main_json:app --reload