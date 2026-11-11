"""
PRODUCTION NOTE: Working through entire process putting in strictly formatted notes
main.py is completely noted
etl_monitor_loop() from orchestration.py is next
I think that notes have caught up with actual build out.

Build out bookmarks:

Not yet started:
NEED pg_check_process_history STILL in main.py
NEED pg_log_process_result STILL in main.py
STILL NEEDS THE pg_get_monitor_locations() in orchestration.py

Pieces stil completely undeveloped to not forget:
How to update the monitoring locations, or remove them.
"""


from datetime import datetime, UTC
from orchestration import etl_monitors_loop

import db_config
import sqlite3

# CHECK PROCESS HISTORY, NEEDED TO DETERMINE WHICH TYPE OF RUN TO PERFORM
def sqlite_check_process_history(CONNECTION_DETAILS_INNER):
    print(f"[DEBUG] ({datetime.now()}) sqlite_check_process_history(): Start of function. Params: CONNECTION_DETAILS_INNER={CONNECTION_DETAILS_INNER}")
    
    DB_PATH = CONNECTION_DETAILS_INNER
    db_conn = sqlite3.connect(DB_PATH)
    db_cursor = db_conn.cursor()

    # Get start of day & start of month
    now = datetime.now(UTC)
    start_of_today = now.replace(hour=0, minute= 0, second=0, microsecond= 0)
    start_of_month = start_of_today.replace(day=1)

    print(f"[INFO] ({datetime.now()}) sqlite_check_process_history(): Checking hisotry based on start_of_today={start_of_today}, and start_of_month={start_of_month}")

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
    print(f"[INFO] ({datetime.now()}) sqlite_check_process_history(): has_monthly_run={has_monthly_run}")
    

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
    print(f"[INFO] ({datetime.now()}) sqlite_check_process_history(): has_daily_run={has_daily_run}")
    
    db_conn.close()

    daily_monthly_status = {
        "has_daily_run": has_daily_run,
        "has_monthly_run": has_monthly_run,
    } 

    print(f"[DEBUG] ({datetime.now()}) sqlite_check_process_history(): End of function. Returning: daily_monthly_status={daily_monthly_status} as dict")
    return daily_monthly_status


####
####    NEED pg_check_process_history STILL
####




############### UPDATE PROCESS HISTORY WITH RESULTS FROM THIS RUN
# Sqlite Version
def sqlite_log_process_results(process_dict_inner, CONNECTION_DETAILS_INNER):
    print(f"[DEBUG] ({datetime.now()}) sqlite_log_process_results(): Start of function. Params: process_dict_inner={process_dict_inner}; CONNECTION_DETAILS_INNER={CONNECTION_DETAILS_INNER}")
    DB_PATH = CONNECTION_DETAILS_INNER

    # Start SQLITE Connection & Cursor
    db_conn = sqlite3.connect(DB_PATH)
    db_cursor = db_conn.cursor()

    # Prepare row to log from passed in parameter, and change timestamps to text for sqlite
    log_row = dict(process_dict_inner)

    log_row["started_at"] = log_row["started_at"].isoformat()
    log_row["finished_at"] = log_row["finished_at"].isoformat()

    # SQL code to upload the process result
    upload_process_result = """
        INSERT INTO rivers_process_history
            (job_type, started_at, finished_at, is_successful, successful_monitor_pulls, failed_monitor_pulls, rows_upserted, error_message)
        VALUES 
            (:job_type, :started_at, :finished_at, :is_successful, :successful_monitor_pulls, :failed_monitor_pulls, :rows_upserted, :error_message)
        ;"""

    db_cursor.execute(upload_process_result, log_row)
    print(f"[DEBUG] ({datetime.now()}) sqlite_log_process_results(): results inserted to sqlite database. Row uploaded: process_dict_inner={process_dict_inner}")
    
    db_conn.commit()
    print(f"[DEBUG] ({datetime.now()}) sqlite_log_process_results(): insert committed.")
    
    db_conn.close()
    print(f"[DEBUG] ({datetime.now()}) sqlite_log_process_results(): End of Function. No Return.")


####
####    NEED pg_log_process_result STILL
####





######## MAIN ETL FUNCTION - RUNS ORCHESTRATION FUNCTION AND LOGS THE RESULT
def main_etl(DB_TYPE, CONNECTION_DETAILS, run_type):
    print(f"[DEBUG] ({datetime.now()}) main_etl(): Start of Function. Params: DB_TYPE={DB_TYPE}; CONNECTION_DETAILS={CONNECTION_DETAILS}; run_type={run_type}")

    if run_type == "15-minute":
        time_frame = "PT3H"
    elif run_type == "daily":
        time_frame = "P3D"
    elif run_type == "monthly":
        time_frame = "P9M"
    print(f"[DEBUG] ({datetime.now()}) main_etl(): time_frame ={time_frame}")

    error_message = ""
    start_timestamp = datetime.now(UTC)
    try:
        print(f"[DEBUG] ({datetime.now()}) main_etl(): Calling etl_monitors_loop(). DB_TYPE = {DB_TYPE}; CONNECTION_DETAILS = {CONNECTION_DETAILS}; time_frame = {time_frame}")
        
        successful_monitoring_locations, failed_monitoring_locations, rows_uploaded = etl_monitors_loop(DB_TYPE, CONNECTION_DETAILS, time_frame)
        stop_timestamp = datetime.now(UTC)
        print(f"[DEBUG] ({datetime.now()}) main_etl: etl_monitors_loop() finished and returned: successful_monitoring_locations={successful_monitoring_locations}; failed_monitoring_locations={failed_monitoring_locations}; rows_uploaded={rows_uploaded}")
        print(f"[DEBUG] ({datetime.now()}) main_etl(): etl_monitor_loop() timestamps: start_timestamp={start_timestamp}; stop_timestamp={stop_timestamp}")
        
        if successful_monitoring_locations > 0 and rows_uploaded > 0:
            is_successful_run = 1
            print(f"[INFO] ({datetime.now()}) main_etl: etl_monitors_loop() succeeded. successful_monitoring_locations={successful_monitoring_locations}; failed_monitoring_locations={failed_monitoring_locations}; rows_uploaded={rows_uploaded}")
        else:
            is_successful_run = 0
            print(f"[WARNING] ({datetime.now()}) main_etl: etl_monitors_loop() finished with no successful uploads. Successful_monitoring_locations={successful_monitoring_locations}; failed_monitoring_locations={failed_monitoring_locations}; rows_uploaded={rows_uploaded}")
            error_message = f"0 Rows uploaded, 0 locations successful."

    except Exception as e:
        stop_timestamp = datetime.now(UTC)
        successful_monitoring_locations = 0
        failed_monitoring_locations = 0
        rows_uploaded = 0
        is_successful_run = 0
        error_message = f"Error: {e}"
        print(f"[WARNING] ({datetime.now()}) main_etl: code failure in try/except around etl_monitors_loop(). Error: {e}")


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
        print(f"[DEBUG] ({datetime.now()}) main_etl(): Calling sqlite_log_process_results(). results_dict={results_dict}; CONNECTION_DETAILS={CONNECTION_DETAILS}")
        sqlite_log_process_results(results_dict, CONNECTION_DETAILS)
    elif DB_TYPE == "postgresql":
        # LEAVE SPOT FOR POSTGRESQL VERSION ONCE IT IS CREATED
        # print(f"[DEBUG] ({datetime.now()}) main_etl(): Calling sqlite_log_process_results(). results_dict={results_dict}; CONNECTION_DETAILS={CONNECTION_DETAILS}")
        pass

    print(f"[DEBUG] ({datetime.now()}) main_etl(): End of Function. No Return")



    

    









if __name__ == "__main__":
    print(f"[DEBUG] ({datetime.now()}) main: Opening of main. '__name__' == '__main__'")
    
    # Get DB_TYPE, CONNECTION_DETAILS, and historical_run_check
    DB_TYPE = db_config.get_database_type()
    CONNECTION_DETAILS = db_config.get_database_connection(DB_TYPE)
    if DB_TYPE == "sqlite":
        print(f"[DEBUG] ({datetime.now()}) main: Calling sqlite_check_process_history().")
        historical_run_check = sqlite_check_process_history(CONNECTION_DETAILS)
    elif DB_TYPE == "postgresql":
        # Leave for when historical run check for pg has been made
        # print(f"[DEBUG] ({datetime.now()}) main: Calling sqlite_check_process_history().")
        pass

    print(f"[INFO] ({datetime.now()}) main: DB_TYPE = {DB_TYPE}; Historical Run Check: {historical_run_check}; CONNECTION_DETAILS: {CONNECTION_DETAILS}")

    # 15 MINUTE RUN 
    run_type = "15-minute"
    print(f"[DEBUG] ({datetime.now()}) main: Calling main_etl(). DB_TYPE = {DB_TYPE}; run_type: {run_type}; CONNECTION_DETAILS: {CONNECTION_DETAILS}")
    main_etl(DB_TYPE, CONNECTION_DETAILS, run_type)

    # Daily Run
    if historical_run_check["has_daily_run"] == False:
        run_type = "daily"
        print(f"[DEBUG] ({datetime.now()}) main: Calling main_etl(). DB_TYPE = {DB_TYPE}; run_type: {run_type}; CONNECTION_DETAILS: {CONNECTION_DETAILS}")
        main_etl(DB_TYPE, CONNECTION_DETAILS, run_type)

    # Monthly Run
    if historical_run_check["has_monthly_run"] == False:
        run_type = "monthly"
        print(f"[DEBUG] ({datetime.now()}) main: Calling main_etl(). DB_TYPE = {DB_TYPE}; run_type: {run_type}; CONNECTION_DETAILS: {CONNECTION_DETAILS}")
        main_etl(DB_TYPE, CONNECTION_DETAILS, run_type)





