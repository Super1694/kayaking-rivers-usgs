"""
WHO AM I:       A .py module that gathers the .env variables for both SQLite and PostgreSQL based projects

HOW AM I:       Just some simple if-then type logic
"""

# Imports
import os
from pathlib import Path

from dotenv import load_dotenv

# Load variables from .env
load_dotenv()


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
    DB_FOLDER = get_sqlite_db_location()
    DB_FILENAME = get_sqlite_db_name()
    DB_PATH = DB_FOLDER / DB_FILENAME

    return DB_PATH


#Quick Test
full_path = get_sqlite_full_path()
print(full_path)