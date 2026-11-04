
import psycopg


############# SQLITE VERSION





############# POSTGRES VERSION
def pg_readings_upload (features_list : list, CONNECTION_DETAILS_INNER : dict):
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


