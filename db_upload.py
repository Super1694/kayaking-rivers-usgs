
import psycopg
import sqlite3
from datetime import datetime, UTC


############# SQLITE VERSION

def sqlite_readings_upsert(CONNECTION_DETAILS_INNER, features_list : list):
    print(f"[DEBUG] ({datetime.now(UTC)}) sqlite_readings_upsert(): Start of Function. Params: len(features_list)={len(features_list)}; CONNECTION_DETAILS_INNER={CONNECTION_DETAILS_INNER}")

    readings = [dict(r) for r in features_list]
    DB_PATH = CONNECTION_DETAILS_INNER

    # MODIFY FEATURES_LIST TO WORK WITH SQLITE VARIABLES
    for reading in readings:
        if reading["reading_time"]:
            reading["reading_time"] = reading["reading_time"].isoformat()
        if reading["value"] is not None:
            reading["value"] = float(reading["value"])
        if reading["org_last_modified"]:
            reading["org_last_modified"] = reading["org_last_modified"].isoformat()
        if reading["pull_time"]:
            reading["pull_time"] = reading["pull_time"].isoformat()
    print(f"[DEBUG] ({datetime.now(UTC)}) sqlite_readings_upsert(): variable types adjusted for SQLite.")

    db_conn = None
    try:
        db_conn = sqlite3.connect(DB_PATH)
        db_cursor = db_conn.cursor()
        upsert_river_readings = """
            INSERT INTO rivers_river_readings (
                reading_id,
                time_series_id,
                monitor_location_id,
                reading_time,
                value,
                unit,
                parameter_code,
                statistic_id,
                approval_status,
                qualifier,
                org_last_modified,
                collecting_org,
                pull_source,
                pull_time)
            VALUES (
                :reading_id,
                :time_series_id,
                :monitor_location_id,
                :reading_time,
                :value,
                :unit,
                :parameter_code,
                :statistic_id,
                :approval_status,
                :qualifier,
                :org_last_modified,
                :collecting_org,
                :pull_source,
                :pull_time)
            ON CONFLICT (reading_id)
            DO UPDATE SET
                time_series_id = EXCLUDED.time_series_id,
                monitor_location_id = EXCLUDED.monitor_location_id,
                reading_time = EXCLUDED.reading_time,
                value = EXCLUDED.value,
                unit = EXCLUDED.unit,
                parameter_code = EXCLUDED.parameter_code,
                statistic_id = EXCLUDED.statistic_id,
                approval_status = EXCLUDED.approval_status,
                qualifier = EXCLUDED.qualifier,
                org_last_modified = EXCLUDED.org_last_modified,
                collecting_org = EXCLUDED.collecting_org,
                pull_source = EXCLUDED.pull_source,
                pull_time = EXCLUDED.pull_time"""
        print(f"[DEBUG] ({datetime.now(UTC)}) sqlite_readings_upsert(): About to attempt SQL upsert to sqlite database")
        db_cursor.executemany(upsert_river_readings, readings)
        print(f"[INFO] ({datetime.now(UTC)}) sqlite_readings_upsert(): {len(readings)} readings upserted via SQL insert statement.")
        db_conn.commit()
        print(f"[DEBUG] ({datetime.now(UTC)}) sqlite_readings_upsert(): Changes committed to SQLite database")

        rows_upserted = len(readings)
        print(f"[DEBUG] ({datetime.now(UTC)}) sqlite_readings_upsert(): End of Function. Returns rows_upserted={rows_upserted}")
        return rows_upserted
    except sqlite3.OperationalError as e:
        raise sqlite3.OperationalError(f"Error {e}. Looking for db in {DB_PATH} based on .env file.") from e
    finally:
        if db_conn: 
            db_conn.close()


    

    
    



############# POSTGRES VERSION
def pg_readings_upsert (CONNECTION_DETAILS_INNER : dict, features_list : list):
    conn_params = CONNECTION_DETAILS_INNER
    try: 
        sql_conn = psycopg.connect(host = conn_params["host"],
                            port = conn_params["port"],
                            user = conn_params["user"],
                            password = conn_params["password"],
                            dbname = conn_params["dbname"])
    except psycopg.OperationalError as e:
        raise psycopg.OperationalError(f"could not connect to database: {e}") from e

    with sql_conn:
        sql_cursor = sql_conn.cursor()


        try:
            with sql_conn.transaction():
                sql_cursor.executemany("""INSERT INTO rivers.river_readings (
                                    reading_id,
                                    time_series_id,
                                    monitor_location_id,
                                    reading_time, 
                                    value,
                                    unit,
                                    parameter_code,
                                    statistic_id,
                                    approval_status,
                                    qualifier,
                                    org_last_modified,
                                    collecting_org,
                                    pull_source,
                                    pull_time)
                                    VALUES (%(reading_id)s, %(time_series_id)s, %(monitor_location_id)s, 
                                            %(reading_time)s, %(value)s, %(unit)s, %(parameter_code)s, 
                                            %(statistic_id)s, %(approval_status)s, %(qualifier)s, 
                                            %(org_last_modified)s, %(collecting_org)s, %(pull_source)s, %(pull_time)s)
                                    ON CONFLICT (reading_id)
                                    DO UPDATE SET
                                        time_series_id = EXCLUDED.time_series_id,
                                        monitor_location_id = EXCLUDED.monitor_location_id,
                                        reading_time = EXCLUDED.reading_time,
                                        value = EXCLUDED.value,
                                        unit = EXCLUDED.unit,
                                        parameter_code = EXCLUDED.parameter_code,
                                        statistic_id = EXCLUDED.statistic_id,
                                        approval_status = EXCLUDED.approval_status,
                                        qualifier = EXCLUDED.qualifier,
                                        org_last_modified = EXCLUDED.org_last_modified,
                                        collecting_org = EXCLUDED.collecting_org,
                                        pull_source = EXCLUDED.pull_source,
                                        pull_time = EXCLUDED.pull_time
                                        """,features_list)
                                       #,
                                    # (feature["reading_id"]
                                    # ,feature["time_series_id"]
                                    # ,feature["monitor_location_id"]
                                    # ,feature["reading_time"] 
                                    # ,feature["value"]
                                    # ,feature["unit"]
                                    # ,feature["parameter_code"]
                                    # ,feature["statistic_id"]
                                    # ,feature["approval_status"]
                                    # ,feature["qualifier"]
                                    # ,feature["org_last_modified"]
                                    # ,feature["collecting_org"]
                                    # ,feature["pull_source"]
                                    # ,feature["pull_time"]))
                
                
                # DATA VALIDATION
                # Check that upload length matches pull length before committing
                pull_time_to_check = features_list[0]["pull_time"]
                sql_cursor.execute("SELECT pull_time, count(reading_id) as db_upsert_count FROM rivers.river_readings WHERE pull_time = %s GROUP BY pull_time",(pull_time_to_check,))
                sql_check_query = sql_cursor.fetchone()
                upsert_count = sql_check_query[1]
                original_list_count = len(features_list)

                if upsert_count != original_list_count:
                    raise ValueError(f"Upsert count mismatch: Expected {original_list_count} rows to upsert. Database shows {upsert_count} upserted for pull time {pull_time_to_check}. Transaction cancelled")

            print(f"Upserted {upsert_count} rows successfully")
        

        except psycopg.Error as e:
            raise psycopg.Error(f"Upload failed: {e}") from e
        #Note - ValueError from an upsert mismatch will automatically go all the way up to parent function.

        sql_conn.commit()


