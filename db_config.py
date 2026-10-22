"""
WHO AM I:       A .py module that gathers the .env variables for both SQLite and PostgreSQL based projects

HOW AM I:       Just some simple if-then type logic
"""

# Imports
import os
from pathlib import Path

from dotenv import load_dotenv


################## BOTH VERSIONS ##################
def get_database_type():
    load_dotenv()
    DB_TYPE = os.getenv("DB_TYPE")
    print(DB_TYPE)
    return DB_TYPE


################## SQLITE VERSION ##################
# CHECK DATABASE LOCATION
def get_sqlite_db_location():
    PROJECT_DIR = Path(__file__).resolve().parent       # DEFAULT Location, absent a User Defined
    CUSTOM_DIR = os.getenv("DB_PARENT_DIRECTORY")       # Grab the User Defined from .env

    # Check User Defined, if null use DEFAULT location
    if CUSTOM_DIR:
        DB_FOLDER = Path(CUSTOM_DIR).expanduser()
        if not DB_FOLDER.is_absolute():
            raise ValueError(
                f"DB_PARENT_DIRECTORY must be a full path, got {CUSTOM_DIR}"
            )
        if not DB_FOLDER.is_dir():
            raise ValueError(
                f"DB_PARENT_DIRECTORY points to {CUSTOM_DIR}, which does not exist.\nPlease ensure DB_PARENT_DIRECTORY points to an existing directory")
    else:
        DB_FOLDER = PROJECT_DIR

    return DB_FOLDER

# CHECK DATABASE NAME
def get_sqlite_db_name():
    DB_FILENAME = os.getenv("DB_FILENAME")                  # Grab DB_FILENAME

    if not DB_FILENAME:
        raise ValueError("DB_FILENAME is not set in .env.\nEnsure .env was from .env.sqlite_example and renamed as '.env' with no leading characters")
    if not DB_FILENAME.endswith(".db"):
        raise ValueError(f"DB_FILENAME must end in .db, got {DB_FILENAME}")

    return DB_FILENAME

# FINALIZE DATABASE FULL PATH
def get_sqlite_full_path():
    # Load variables from .env
    load_dotenv()

    DB_FOLDER = get_sqlite_db_location()
    DB_FILENAME = get_sqlite_db_name()
    DB_PATH = DB_FOLDER / DB_FILENAME

    return DB_PATH




################## POSTGRESQL VERSION ##################
def get_postgres_db_params():
    # Load variables from .env
    load_dotenv()


    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")

    if not DB_HOST:
        raise ValueError(
            "DB_HOST is not set. Copy the PostgreSQL example file to .env first, and set the database parameters."
        )

    DB_PARAMS = {"host" : DB_HOST,
                 "port" : DB_PORT,
                 "user" : DB_USER,
                 "password" : DB_PASSWORD,
                 "dbname" : DB_NAME}
    return DB_PARAMS