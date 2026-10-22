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
import psycopg
import json

from db_config import get_postgres_db_params, get_database_type, get_sqlite_full_path


############################### FOR BOTH SQLITE & POSTGRESQL #########################################
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
# Create table rivers_monitoring_locations
def sqlite_create_monitoring_locations(DB_PATH_INNER):
    db_conn = sqlite3.connect(DB_PATH_INNER)
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
    print(f"rivers_monitoring_locaitons table available in {DB_PATH_INNER}")

# Upsert from monitors_to_upload to rivers_monitoring_locations
def sqlite_upload_location(DB_PATH_INNER, monitor_locations_data):
    # Connect to Database
    db_conn = sqlite3.connect(DB_PATH_INNER)
    db_cursor = db_conn.cursor()

    upsert_monitor_locations = """
    INSERT INTO rivers_monitoring_locations 
        (location_name,reporting_org,org_monitor_id,org_api_root,is_active)
    VALUES
        (:location_name, :reporting_org, :org_monitor_id, :org_api_root, :is_active)
    ON CONFLICT (reporting_org, org_monitor_id)
    DO UPDATE SET
        location_name = EXCLUDED.location_name,
        org_api_root = EXCLUDED.org_api_root,
        is_active = EXCLUDED.is_active
    ;
    """

    db_cursor.executemany(upsert_monitor_locations, monitor_locations_data)
    db_conn.commit()
    db_conn.close()
    print(f"rivers_monitoring_locations has just had {len(monitor_locations_data)} upserted")

# Create rivers_river_readings table in SQLite

def sqlite_create_river_readings(DB_PATH_INNER):
    db_conn = sqlite3.connect(DB_PATH_INNER)
    db_cursor = db_conn.cursor()
    create_table2 = """
    CREATE TABLE IF NOT EXISTS rivers_river_readings(
        reading_id TEXT PRIMARY KEY NOT NULL,
        time_series_id TEXT,
        monitor_location_id TEXT NOT NULL,
        reading_time TEXT NOT NULL,
        value REAL NOT NULL,
        unit TEXT NOT NULL,
        parameter_code TEXT,
        statistic_id TEXT,
        approval_status TEXT,
        qualifier TEXT,
        org_last_modified TEXT,
        collecting_org TEXT,
        pull_source TEXT,
        pull_time TEXT
    );
    """
    db_cursor.execute(create_table2)
    db_conn.close()
    
def sqlite_full_initialization(DB_PATH_OUTER):
    # Get monitor locations from JSON
    monitor_locations = get_monitor_data()

    # Create rivers_monitoring_locations table and upsert monitors
    sqlite_create_monitoring_locations(DB_PATH_OUTER)
    sqlite_upload_location(DB_PATH_OUTER,monitor_locations)

    # Create rivers_river_readings table
    sqlite_create_river_readings(DB_PATH_OUTER)


# # SQLITE TEST ZONE
# from db_config import get_sqlite_full_path
# DB_PATH = get_sqlite_full_path()
# sqlite_full_initialization(DB_PATH)


# check_conn = sqlite3.connect(DB_PATH)
# check_curs = check_conn.cursor()
# # TABLES CREATED CHECK
# check_curs.execute("SELECT name FROM sqlite_master WHERE type = 'table';")
# print(check_curs.fetchall())


# # MONITORING LOCATIONS TABLE CHECK
# select_all_sql = """SELECT * FROM rivers_monitoring_locations"""
# check_curs.execute(select_all_sql)
# check_data = check_curs.fetchall()
# print(check_data)





# ##################### POSTGRES VERSION ############################
# Note - User must have previously created the Server & Database, and put 
# the connection parameters in the .env file created based on .env.example_postgresql



# Create Schema
def pg_create_schema(DB_PARAMS_INNER):
    try:
        db_conn = psycopg.connect(host = DB_PARAMS_INNER["host"],
                                port = DB_PARAMS_INNER["port"],
                                user = DB_PARAMS_INNER["user"],
                                password = DB_PARAMS_INNER["password"],
                                dbname = DB_PARAMS_INNER["dbname"])
    except psycopg.OperationalError as e:
        raise psycopg.OperationalError(f"could not connect to database: {e}") from e

    with db_conn:
        db_cursor = db_conn.cursor()
        pg_create_schema = """CREATE SCHEMA IF NOT EXISTS rivers"""
        db_cursor.execute(pg_create_schema)
    print("Schema Created Succesfully")

def pg_create_monitoring_locations(DB_PARAMS_INNER):
    try:
        db_conn = psycopg.connect(host = DB_PARAMS_INNER["host"],
                                port = DB_PARAMS_INNER["port"],
                                user = DB_PARAMS_INNER["user"],
                                password = DB_PARAMS_INNER["password"],
                                dbname = DB_PARAMS_INNER["dbname"])
    except psycopg.OperationalError as e:
        raise psycopg.OperationalError(f"could not connect to database: {e}") from e

    with db_conn:
        db_cursor = db_conn.cursor()
        pg_create_table1 = """CREATE TABLE IF NOT EXISTS rivers.monitoring_locations 
                            (
                                location_id serial NOT NULL,
                                location_name character varying(255) COLLATE pg_catalog."default" NOT NULL,
                                reporting_org character varying(64) COLLATE pg_catalog."default" NOT NULL,
                                org_monitor_id character varying(64) COLLATE pg_catalog."default" NOT NULL,
                                org_api_root character varying(255) COLLATE pg_catalog."default" NOT NULL,
                                is_active boolean DEFAULT true,
                                CONSTRAINT monitoring_locations_pkey PRIMARY KEY (location_id),
                                CONSTRAINT unique_org_monitors UNIQUE (reporting_org, org_monitor_id)
                            );
                            """
        db_cursor.execute(pg_create_table1)
    print("Table rivers.monitoring_locations created successfully")

# Upsert from monitors_to_upload to rivers_monitoring_locations
def pg_upload_location(DB_PARAMS_INNER, monitor_locations_data):
    try:
        db_conn = psycopg.connect(host = DB_PARAMS_INNER["host"],
                                port = DB_PARAMS_INNER["port"],
                                user = DB_PARAMS_INNER["user"],
                                password = DB_PARAMS_INNER["password"],
                                dbname = DB_PARAMS_INNER["dbname"])
    except psycopg.OperationalError as e:
        raise psycopg.OperationalError(f"could not connect to database: {e}") from e

    with db_conn:
        db_cursor = db_conn.cursor()
        pg_upsert_monitor_locations = """INSERT INTO rivers.monitoring_locations (
                                            location_name,
                                            reporting_org,
                                            org_monitor_id,
                                            org_api_root,
                                            is_active
                                            )
                                        VALUES (%(location_name)s, %(reporting_org)s, %(org_monitor_id)s, %(org_api_root)s, %(is_active)s)
                                        ON CONFLICT (reporting_org, org_monitor_id)
                                        DO UPDATE SET
                                            location_name = EXCLUDED.location_name,
                                            org_api_root = EXCLUDED.org_api_root,
                                            is_active = EXCLUDED.is_active
                                        ;"""
        db_cursor.executemany(pg_upsert_monitor_locations,monitor_locations_data)
        db_conn.commit()
    print(f"rivers_monitoring_locations has just had {len(monitor_locations_data)} upserted")

def pg_create_river_readings(DB_PARAMS_INNER):
    try:
        db_conn = psycopg.connect(host = DB_PARAMS_INNER["host"],
                                port = DB_PARAMS_INNER["port"],
                                user = DB_PARAMS_INNER["user"],
                                password = DB_PARAMS_INNER["password"],
                                dbname = DB_PARAMS_INNER["dbname"])
    except psycopg.OperationalError as e:
        raise psycopg.OperationalError(f"could not connect to database: {e}") from e

    with db_conn:
        db_cursor = db_conn.cursor()
        pg_create_table2 = """CREATE TABLE IF NOT EXISTS rivers.river_readings
                                (
                                    reading_id character varying(255) COLLATE pg_catalog."default" NOT NULL,
                                    time_series_id character varying(255) COLLATE pg_catalog."default",
                                    monitor_location_id character varying(255) COLLATE pg_catalog."default" NOT NULL,
                                    reading_time timestamp with time zone NOT NULL,
                                    value numeric(11,2) NOT NULL,
                                    unit character varying(16) COLLATE pg_catalog."default" NOT NULL,
                                    parameter_code character varying(16) COLLATE pg_catalog."default",
                                    statistic_id character varying(16) COLLATE pg_catalog."default",
                                    approval_status character varying(64) COLLATE pg_catalog."default",
                                    qualifier character varying(255) COLLATE pg_catalog."default",
                                    org_last_modified timestamp with time zone,
                                    collecting_org character varying(255) COLLATE pg_catalog."default",
                                    pull_source text COLLATE pg_catalog."default",
                                    pull_time timestamp with time zone,
                                    CONSTRAINT river_readings_pkey PRIMARY KEY (reading_id)
                                );
                            """
        db_cursor.execute(pg_create_table2)
    print("Table rivers.river_readings created successfully")

def pg_full_initialization(DB_PARAMS_OUTER):
    # Get monitor locations from JSON
    monitor_locations = get_monitor_data()

    # Create rivers shchema
    pg_create_schema(DB_PARAMS_OUTER)

    #Create rivers.monitoring_locations and upsert monitors
    pg_create_monitoring_locations(DB_PARAMS_OUTER)
    pg_upload_location(DB_PARAMS_OUTER,monitor_locations)

    # Create rivers.river_readings table
    pg_create_river_readings(DB_PARAMS_OUTER)



# # POSTGRESQL TESTING AREA

# DB_PARAMS = get_postgres_db_params()
# pg_full_initialization(DB_PARAMS)



if __name__ == "__main__":
    DB_TYPE = get_database_type()
    if DB_TYPE == "postgresql":
        DB_PARAMS = get_postgres_db_params()
        pg_full_initialization(DB_PARAMS)
    elif DB_TYPE == "sqlite":
        DB_PATH = get_sqlite_full_path()o
        sqlite_full_initialization(DB_PATH)
    else:
        raise Exception("No DB_TYPE found in the .env file. Please check that .env was correctly created")
    


