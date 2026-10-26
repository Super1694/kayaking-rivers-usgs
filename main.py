
from datetime import datetime, UTC
from orchestration import etl_monitors_loop

import db_config
import sqlite3

# CHECK PROCESS HISTORY, NEEDED TO DETERMINE WHICH TYPE OF RUN TO PERFORM
def sqlite_check_process_history():
    DB_PATH = db_config.get_sqlite_full_path()
    db_conn = sqlite3.connect(DB_PATH)
    db_cursor = db_conn.cursor()

    # Get start of day & start of month
    now = datetime.now(UTC)
    start_of_today = now.replace(hour=0, minute= 0, second=0, microsecond= 0)
    start_of_month = start_of_today.replace(day=1)

    # Check for successful month run on process history.
    db_cursor.execute(
        """
        SELECT 1 FROM rivers_process_history
        WHERE job_type = 'monthly'
          AND is_successful = 1
          AND started_at >= ?
        LIMIT 1
        """,
        (start_of_month.isoformat(),),
    )
    # If this returns a non-empty set, then the monthly type HAS been run this month.
    has_monthly_run = db_cursor.fetchone() is not None


    # Check for successful day run on process history.
    db_cursor.execute(
        """
        SELECT 1 FROM rivers_process_history
        WHERE job_type IN ('daily', 'monthly')
          AND is_successful = 1
          AND started_at >= ?
        LIMIT 1
        """,
        (start_of_today.isoformat(),),
    )
    # If this returns a non-empty set, then a daily OR monthly set HAS been run today.
    has_daily_run = db_cursor.fetchone() is not None

    db_conn.close()

    daily_monthly_status = {
        "has_daily_run": has_daily_run,
        "has_monthly_run": has_monthly_run,
    } 

    return daily_monthly_status


####
####    NEED pg_check_process_history STILL
####




############### UPDATE PROCESS HISTORY WITH RESULTS FROM THIS RUN
# Sqlite Version
def sqlite_log_process_results(process_dict_inner):
    DB_PATH = db_config.get_sqlite_full_path()
    db_conn = sqlite3.connect(DB_PATH)
    db_cursor = db_conn.cursor()
    log_row = dict(process_dict_inner)



    log_row["started_at"] = log_row["started_at"].isoformat()
    log_row["finished_at"] = log_row["finished_at"].isoformat()

    upload_process_result = """
        INSERT INTO rivers_process_history
            (job_type, started_at, finished_at, is_successful, successful_monitor_pulls, failed_monitor_pulls, rows_upserted, error_message)
        VALUES 
            (:job_type, :started_at, :finished_at, :is_successful, :successful_monitor_pulls, :failed_monitor_pulls, :rows_upserted, :error_message)
        ;"""

    db_cursor.execute(upload_process_result, log_row)
    db_conn.commit()
    db_conn.close()
    print(f"Message from sqlite_log_process_results function. Process result logged to {DB_PATH} in table rivers_process_history")





# Not sure what description to write here
def etl_and_log(DB_TYPE, run_type):
    if run_type == "15-minute":
        time_frame = "PT3H"
    elif run_type == "daily":
        time_frame = "P3D"
    elif run_type == "monthly":
        time_frame = "P9M"

    print(f"Message from etl_and_log function. time_frame: {time_frame}")
    error_message = ""
    start_timestamp = datetime.now(UTC)
    try:
        successful_monitoring_locations, failed_monitoring_locations, rows_uploaded = etl_monitors_loop(DB_TYPE, time_frame)
        stop_timestamp = datetime.now(UTC)
        if successful_monitoring_locations > 0 and rows_uploaded > 0:
            is_successful_run = 1
        else:
            is_successful_run = 0
            error_message = f"0 Rows uploaded, 0 locations successful."
    except Exception as e:
        stop_timestamp = datetime.now(UTC)
        successful_monitoring_locations = 0
        failed_monitoring_locations = 0
        rows_uploaded = 0
        is_successful_run = 0
        error_message = f"Error: {e}"

    
    print(f"Message from etl_and_log function. Rows Uploaded: {rows_uploaded}")

        

    # LOG RESULTS
    results_dict = {"job_type" : run_type, 
                    "started_at" : start_timestamp, 
                    "finished_at" : stop_timestamp,
                    "is_successful" : is_successful_run,
                    "successful_monitor_pulls" : successful_monitoring_locations,
                    "failed_monitor_pulls" : failed_monitoring_locations,
                    "rows_upserted" : rows_uploaded,
                    "error_message" : error_message
                    }

    if DB_TYPE == "sqlite":
        sqlite_log_process_results(results_dict)
    elif DB_TYPE == "postgresql":
        # LEAVE SPOT FOR POSTGRESQL VERSION ONCE IT IS CREATED
        pass




    

    









if __name__ == "__main__":
    DB_TYPE = db_config.get_database_type()
    print(f"Message from name == __main__ portion. DB_TYPE: {DB_TYPE}") # TEST ROW
    if DB_TYPE == "sqlite":
        historical_run_check = sqlite_check_process_history()
    elif DB_TYPE == "postgresql":
        # Leave for when historical run check for pg has been made
        pass

    print(f"Message from name == __main__ portion. Historical Run Check: {historical_run_check}") # TEST ROW


    # 15 MINUTE RUN 
    run_type = "15-minute"
    etl_and_log(DB_TYPE, run_type)

    # Daily Run
    if historical_run_check["has_daily_run"] == False:
        run_type = "daily"
        etl_and_log(DB_TYPE, run_type)

    # Monthly Run
    if historical_run_check["has_monthly_run"] == False:
        run_type = "monthly"
        etl_and_log(DB_TYPE, run_type)





