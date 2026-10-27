
import sqlite3
import psycopg

from db_config import get_postgres_db_params, get_sqlite_full_path, get_database_type


######## FUNCTIONS TO GET MONITOR LOCATIONS, SQLITE & POSTGRESQL (pg_)
def sqlite_get_monitor_locations():
    try:
        DB_PATH = get_sqlite_full_path()
        db_conn = sqlite3.connect(DB_PATH)
        db_conn.row_factory = sqlite3.Row
        db_cursor = db_conn.cursor()

        select_active_monitors = """SELECT * 
                                FROM rivers_monitoring_locations 
                                WHERE is_active = 1;"""

        db_cursor.execute(select_active_monitors)
        active_monitors = [dict(row) for row in db_cursor.fetchall()]
    except sqlite3.OperationalError as e:
        raise sqlite3.OperationalError(f"Error {e}. Looking for db in {DB_PATH} based on .env file.") from e
    finally:
        db_conn.close()
    
    return active_monitors

    
#######
####### STILL NEEDS THE pg_get_monitor_locations():
#######



######## FUNCTIONS TO UPDATE  MONITOR LOCATIONS, SQLITE & POSTGRESQL (pg_)





##### MAIN ORCHESTRATION FUNCTION
def usgs_continuous_etl(DB_TYPE_INNER, time_parameter, monitor_row):
    print(f"Message from usgs_continuous_etl function. Received DB_TYPE: {DB_TYPE_INNER}, Time Parameter: {time_parameter}, monitor_row: {monitor_row}")

    monitor_id = monitor_row["org_monitor_id"]
    collecting_org = monitor_row["reporting_org"]
    api_endpoint = monitor_row["org_api_endpoint"]

    # EXTRACT (API Pull)
    rows_uploaded = 0
    for page in usgs_pull_continuous(monitor_id,api_endpoint, time_parameter):
        readings = usgs_transform(page, api_endpoint, collecting_org)

        if DB_TYPE_INNER == "sqlite":
            rows_uploaded += sqlite_river_readings_upsert(readings)
        elif DB_TYPE_INNER == "postgresql":
            # row_uploaded += pg_river_readings_upsert(readings)
            pass


    ## HARDCODED FOR NOW, TO REPLACE WITH VARIABLES
    rows_uploaded = 3

    return rows_uploaded









def etl_monitors_loop(DB_TYPE_INNER, time_frame_inner):
    print(f"Message from etl_monitors_loop: time frame param: {time_frame_inner}, DB_TYPE: {DB_TYPE_INNER}") # TEST ROW

    if DB_TYPE_INNER == "sqlite":
        monitor_list = sqlite_get_monitor_locations()
    elif DB_TYPE_INNER == "postgresql":
        # HOLD FOR WHEN pg_get_monitor_locations() is written
        pass

    successful_monitoring_locations = 0
    failed_monitoring_locations = 0
    rows_uploaded = 0

    for monitor in monitor_list:
        #print(monitor) # TEST ROW
        try:
            monitor_rows = usgs_continuous_etl(DB_TYPE_INNER, time_frame_inner, monitor)
            rows_uploaded += monitor_rows
            if monitor_rows > 0:
                successful_monitoring_locations += 1
            else:
                failed_monitoring_locations += 1
        except Exception as e:
            failed_monitoring_locations += 1
            print(f"Monitor {monitor['org_monitor_id']} failed: {e}")

    return successful_monitoring_locations, failed_monitoring_locations, rows_uploaded


    


    
    

