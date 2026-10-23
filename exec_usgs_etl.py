
from datetime import datetime, UTC

import db_config
import sqlite3

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

    return {
        "has_daily_run": has_daily_run,
        "has_monthly_run": has_monthly_run,
    } 











if __name__ == "__main__":
    DB_TYPE = db_config.get_database_type()
    print(DB_TYPE)
    run_checks = sqlite_check_process_history()
    print(run_checks)


