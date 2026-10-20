"""
# WHY AM I:         The main script requires that a database is already setup.

# WHO AM I:         A Python script to create and initialize your SQLite database

# WHAT AM I:        I will:
                    - create a new database, if one does not already exist
                    - Create 2 tables: rivers_monitoring_locations and rivers_river_readings
                    - Add monitor locations to rivers_monitoring_locations table based on monitors_to_upload.json

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
        with open(JSON_PATH, encoding="utf-8-sig") as JSON_HANDLE:
            data_to_return = json.load(JSON_HANDLE)

        # ERROR CHECKING: Check Result, large scale. Is it a list? Is it at least 1 item long?
        if not isinstance(data_to_return, list):
            raise ValueError("monitors_to_upload.json must hold a *list* of *dicts*, where each dict is a monitor")
        if len(data_to_return) == 0:
            raise ValueError(f"Monitors_to_upload is currently empty. Don't worry - a fresh example of what should be in there is in .monitors.example. Copy and paste it into monitors_to_upload.json and try again")

        # Check the data entered for each entry
        for monitor_count, item in enumerate(data_to_return, start=1):
            try: 
                if not isinstance(item,dict):
                    raise ValueError(f"Monitor {monitor_count} is not a DICT, as required. Check monitors_to_upload.json")
                if not isinstance(item["location_name"], str) or not item["location_name"].strip():
                    raise ValueError(f"monitor {monitor_count}: location_name is a REQUIRED field. Must be TEXT")
                if not isinstance(item["reporting_org"], str) or not item["reporting_org"].strip():
                    raise ValueError(f"monitor {monitor_count}: reporting_org is a REQUIRED field. Must be TEXT")
                if not isinstance(item["org_monitor_id"], str) or not item["org_monitor_id"].strip():
                    raise ValueError(f"monitor {monitor_count}: org_monitor_id is a REQUIRED field. Must be TEXT")
                if not isinstance(item["org_api_root"], str) or not item["org_api_root"].strip():
                    raise ValueError(f"monitor {monitor_count}: org_api_root is a REQUIRED field. Must be TEXT")
                if not isinstance(item["is_active"], bool):
                    raise ValueError(f"monitor {monitor_count}: is_active is a REQUIRED field. Must be true or false")
            except KeyError as e:
                raise KeyError(f"required key/value pair missing for monitor {monitor_count}: {e.args[0]} ")

        # PLACEHOLDER - put the API Call function in here to check that it works with the data from this monitor.

    # ERROR HANDLING

    except FileNotFoundError as e:
        raise FileNotFoundError(f"json name or location has been changed. Ensure that monitors_to_upload.json name remains unchanged: {e}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"monitors_to_upload.json has a syntax error on line {e.lineno}: {e.msg}") from e

    # Return the data
    return data_to_return



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

    

