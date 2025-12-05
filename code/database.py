import os
import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

MAX_RETRIES = 10
TOTAL_TIMEOUT = 60
DELAY_BETWEEN_RETRIES = TOTAL_TIMEOUT / MAX_RETRIES

# Variable globale pour Base
Base = declarative_base()

def get_db_engine():
    database_url = os.getenv(
        "DATABASE_URL",  # Utilisez "DATABASE_URL" pour être cohérent avec les conventions
        "mysql+pymysql://wine_user:secure_password@localhost:3306/wine_cellar"
    )
    logger.info("##### DATABASE_URL = %s ######", database_url)
    return create_engine(database_url, pool_pre_ping=True)

def get_db_session():
    engine = get_db_engine()
    sessionlocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return sessionlocal()

def init_db():
    engine = get_db_engine()
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("[database] Connected to DB on attempt %s", attempt)
            Base.metadata.create_all(bind=engine)  # Crée les tables définies dans les modèles
            sessionlocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            return sessionlocal
        except SQLAlchemyError:
            logger.warning("Error connecting to DB: %s - Retry in %s", attempt,
                           DELAY_BETWEEN_RETRIES)
            time.sleep(DELAY_BETWEEN_RETRIES)
    logger.error("Failed to connect to DB after %s attempts", MAX_RETRIES)
    raise RuntimeError("Failed to connect to the database")

def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()

# Initialisez la base de données et obtenez une session
session_local = init_db()