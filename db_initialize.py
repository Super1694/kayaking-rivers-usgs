"""
# WHY AM I:         The main script requires that a database is already setup.

# WHO AM I:         A Python script to create and initialize your SQLite database

# WHAT AM I:        I will:
                    - create a new database, if one does not already exist
                    - Create 2 tables: rivers_monitoring_locations and rivers_river_readings
                    - Add 1 monitor location to rivers_monitoring_locations table

"""

from pathlib import Path
import sqlite3
import json


from db_config import get_sqlite_full_path
DB_PATH = get_sqlite_full_path()


# Get Monitor Data from JSON
def get_monitor_data():
    try:
        JSON_PATH = Path(__file__).resolve().parent / "monitors_to_upload.json"
        JSON_HANDLE = open(JSON_PATH)
        data_to_return = json.load(JSON_HANDLE)
        if not isinstance(data_to_return, list):
            raise ValueError("monitors_to_upload.json must hold a *list* of *dicts*, where each dict is a monitor")
        

        # Check the data entered
        # PLACEHOLDER - put the API Call function in here to check that it works with the data from this monitor.
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Syntax error in monitors_to_upload.json: {e}") from e
    

    # Return the data
    return data_to_return

data = get_monitor_data()
print(type(data))








# ##################### SQLITE VERSION ############################
# Create rivers_monitoring_locations
def sqlite_create_monitoring_locations():
    db_conn = sqlite3.connect(DB_PATH)
    db_cursor = db_conn.cursor()

    # SQL Code to create the SQLite data table for monitor locations:
    create_table1 = """
    CREATE TABLE IF NOT EXISTS rivers_monitoring_locations(
        location_id INTEGER PRIMARY KEY,
        location_name TEXT NOT NULL,
        reporting_org TEXT NOT NULL,
        org_monitor_id TEXT NOT NULL,
        org_api_root TEXT NOT NULL,
        is_active INTEGER DEFAULT 1 NOT NULL CHECK (is_active IN (0, 1)),
        UNIQUE (reporting_org, org_monitor_id)
    );
    """
    db_cursor.execute(create_table1)
    db_conn.commit()
    db_conn.close()
    print(f"Rivers_monitoring_locaitons table available in {DB_PATH}")


def sqlite_upload_location():
    db_conn = sqlite3.connect(DB_PATH)
    db_cursor = db_conn.cursor()

    

