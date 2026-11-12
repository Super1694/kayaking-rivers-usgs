
import sqlite3
import psycopg
from datetime import datetime, UTC

from usgs_api import usgs_pull_continuous, usgs_transform
from db_upload import sqlite_readings_upsert



######## FUNCTIONS TO GET MONITOR LOCATIONS, SQLITE & POSTGRESQL (pg_)
def sqlite_get_monitor_locations(CONNECTION_DETAILS_INNER):
    try:
        DB_PATH = CONNECTION_DETAILS_INNER
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





##### ETL ORCHESTRATION FUNCTION @ MONITOR LEVEL
def usgs_continuous_etl(DB_TYPE_INNER, CONNECTION_DETAILS_INNER, time_parameter, monitor_row):
    print(f"[DEBUG] ({datetime.now(UTC)}) usgs_continuous_etl(): Start of function. Params: DB_TYPE_INNER={DB_TYPE_INNER}; CONNECTION_DETAILS_INNER={CONNECTION_DETAILS_INNER}; time_parameter={time_parameter}; monitor_row={monitor_row}")
    
    monitor_id = monitor_row["org_monitor_id"]
    collecting_org = monitor_row["reporting_org"]
    api_endpoint = monitor_row["org_api_endpoint"]
    start_pull_timestamp = datetime.now(UTC)
    print(f"[INFO] ({datetime.now(UTC)}) usgs_continuous_etl(): Key parameters for other function calls: monitor_id={monitor_id}; collecting_org={collecting_org}; api_endpoint={api_endpoint}; start_pull_timestamp={start_pull_timestamp}")
    

    # EXTRACT (API Pull)
    print(f"[DEBUG] ({datetime.now(UTC)}) usgs_continuous_etl(): Calling usgs_pull_continuous() -> generator.")
    
    rows_uploaded = 0
    for page in usgs_pull_continuous(monitor_id,api_endpoint, time_parameter):
        print(f"[DEBUG] ({datetime.now(UTC)}) usgs_continuous_etl() inside for loop: Calling usgs_transform()")
        readings = usgs_transform(page, api_endpoint, collecting_org,start_pull_timestamp) #returns a list of dicts
        print(f"[INFO] ({datetime.now(UTC)}) usgs_continuous_etl() inside for loop: number of readings={len(readings)} (just for this batch of yielded results in the for loop. Not total)")

        if DB_TYPE_INNER == "sqlite":
            # print(f"[BUILDING] ({datetime.now(UTC)}) THIS WOULD NOW RUN db_upload.sqlite_river_readings_upsert()")
            # rows_uploaded += 5 #PLACEHOLDER
            print(f"[DEBUG] ({datetime.now(UTC)}) usgs_continuous_etl(): Calling sqlite_readings_upsert.")
            uploads = sqlite_readings_upsert(CONNECTION_DETAILS_INNER, readings)
            rows_uploaded += uploads
            print(f"[INFO] ({datetime.now(UTC)}) usgs_continuous_etl() inside for loop: Batch of readings uploaded. Running total rows_uploaded={rows_uploaded}")
            
            
        elif DB_TYPE_INNER == "postgresql":
            # row_uploaded += pg_river_readings_upsert(readings)
            pass

    print(f"[INFO] ({datetime.now(UTC)}) usgs_continuous_etl(): Total rows_uploaded={rows_uploaded}")
    print(f"[DEBUG] ({datetime.now(UTC)}) usgs_continuous_etl(): End of Function. Returns total rows_uploaded={rows_uploaded}")
    return rows_uploaded









def etl_monitors_loop(DB_TYPE_INNER, CONNECTION_DETAILS_INNER, time_frame_inner):
    print(f"[DEBUG] ({datetime.now(UTC)}) etl_monitor_loop(): Start of function. Params: DB_TYPE_INNER={DB_TYPE_INNER}; CONNECTION_DETAILS_INNER={CONNECTION_DETAILS_INNER}; time_frame_inner={time_frame_inner}")

    if DB_TYPE_INNER == "sqlite":
        print(f"[DEBUG] ({datetime.now(UTC)}) etl_monitor_loop(): Start of function. Calling sqlite_get_monitor_locations()")
        monitor_list = sqlite_get_monitor_locations(CONNECTION_DETAILS_INNER)
    elif DB_TYPE_INNER == "postgresql":
        # print(f"[DEBUG] ({datetime.now(UTC)}) etl_monitor_loop(): Start of function. Calling sqlite_get_monitor_locations()")
        # HOLD FOR WHEN pg_get_monitor_locations() is written
        pass

    #Initialize loop variables
    successful_monitoring_locations = 0
    failed_monitoring_locations = 0
    rows_uploaded = 0

    #Begin Loop
    print(f"[INFO] ({datetime.now(UTC)}) etl_monitor_loop(): Number of Monitor Locations returned = {len(monitor_list)}. Beginning loop through monitors")
    for monitor in monitor_list:
        print(f"[DEBUG] ({datetime.now(UTC)}) etl_monitor_loop(): Inside of for loop. Monitor = {monitor}")
        try:
            print(f"[DEBUG] ({datetime.now(UTC)}) etl_monitor_loop(): Calling usgs_continuous_etl().")
            monitor_rows = usgs_continuous_etl(DB_TYPE_INNER, CONNECTION_DETAILS_INNER, time_frame_inner, monitor)
            rows_uploaded += monitor_rows
            
            if monitor_rows > 0:
                successful_monitoring_locations += 1
                print(f"[INFO] ({datetime.now(UTC)}) etl_monitor_loop(): After usgs_continous_etl. Monitor results: successful with {monitor_rows} rows uploaded.")
            else:
                failed_monitoring_locations += 1

            print(f"[INFO] ({datetime.now(UTC)}) etl_monitor_loop(): Running total: rows_uploaded={rows_uploaded}; successful_monitoring_locations={successful_monitoring_locations}; failed_monitoring_locations={failed_monitoring_locations}")
        except ValueError as e:
            failed_monitoring_locations += 1
            print(f"[WARNING] ({datetime.now(UTC)}) etl_monitor_loop(): Inside of for loop. Code failure/exception thrown. Monitor {monitor['org_monitor_id']} failed: {e}")

    print(f"[DEBUG] ({datetime.now(UTC)}) etl_monitor_loop(): End of Function. Returns: successful_monitoring_locations={successful_monitoring_locations}; failed_monitoring_locations={failed_monitoring_locations}; rows_uploaded={rows_uploaded}")
    return successful_monitoring_locations, failed_monitoring_locations, rows_uploaded

