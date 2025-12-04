#!/bin/bash

clear
docker compose down
docker compose up --build
# clear && uvicorn main:app --reload
# cd code && 
# uvicorn code.main:app --reload

