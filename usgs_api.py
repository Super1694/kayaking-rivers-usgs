
import requests

from collections.abc import Iterator
import requests
import json
from datetime import datetime, UTC
from decimal import Decimal, InvalidOperation

def usgs_pull_continuous(monitor_id_inner: str, api_endpoint_inner: str, time_parameter_inner: str):
    # print(f"Message from usgs_pull Continuous. monitor_id: {monitor_id_inner}, api_endpoint: {api_endpoint_inner}, time_parameter: {time_parameter_inner}")
    try:
        usgs_params = {"time" : time_parameter_inner, 
                    "limit" : 10000,
                    "monitoring_location_id" : monitor_id_inner
                    }
        response = requests.get(api_endpoint_inner, params=usgs_params, timeout=30)
        response.raise_for_status()
        print(f"API call for {monitor_id_inner} to {api_endpoint_inner} returned response {response.status_code}")

        yield response
        next_url = None
        for link in response.json()["links"]:
            if link["rel"] == "next":
                next_url = link["href"]

        while next_url != None:
            response = requests.get(next_url, timeout=30)
            response.raise_for_status()
            print(f"API call for {monitor_id_inner} to {api_endpoint_inner} returned response {response.status_code}")
            yield response
            next_url = None
            for link in response.json()["links"]:
                    if link["rel"] == "next":
                        next_url = link["href"]
    except requests.exceptions.HTTPError as e:
         raise requests.exceptions.RequestException(f"Pull failed for monitor {monitor_id_inner} from {api_endpoint_inner}: {e}") from e

    except requests.exceptions.Timeout as e:
         raise requests.exceptions.Timeout(f"Pull failed for monitor {monitor_id_inner} from {api_endpoint_inner}: {e}") from e



    


############# Transform API Calls to list of dictionaries
def usgs_transform(api_response, api_endpoint: str ,collecting_org: str):
    start_time = datetime.now(UTC)
    
    try:
        features = api_response.json()["features"]
        print(f"'features' key extracted from GeoJSON returned by API Call")
    except KeyError as e:
        raise KeyError(f"Response missing expected 'features' structure: {e}") from e
    except ValueError as e:
        raise ValueError(f"This API call did not return a GeoJSON as expected: {e}") from e

    features_length = len(features)
    if features_length == 0:
        raise ValueError(f"API call to {api_endpoint} returned empty set of features")

    return_items = []
    for feature in features:
        # print(feature)
        # print('\n')

        try:   

            raw = feature["properties"]

            if feature["id"] is None:
                raise ValueError("Null value in required field: reading_id")
            elif len(feature["id"]) > 255:
                raise ValueError("Reading_id exceeds max field length")
            else:
                reading_id = str(feature["id"])

            if raw["time_series_id"] is None:
                time_series_id = None
                print(f"time_series_id returned NULL for reading {reading_id}")
            elif len(raw["time_series_id"]) > 255:
                time_series_id = str(raw["time_series_id"])[:255]
                print(f"time_series_id exceeded max length, truncated for reading {reading_id}")
            else:
                time_series_id = str(raw["time_series_id"])

            if raw["monitoring_location_id"] is None:
                raise ValueError("Null value in required field: monitor_location_id")
            elif len(raw["monitoring_location_id"]) > 255:
                raise ValueError("monitor_location_id exceeds max field length")
            else:
                monitor_location_id = str(raw["monitoring_location_id"])

            if raw["time"] is None:
                raise ValueError("Null value in required field: reading_time")
            else:
                reading_time = datetime.fromisoformat(raw["time"])

            if raw["value"] is None:
                raise ValueError("Null value in required field: value")
            else:
                value = Decimal(raw["value"])

            if raw["unit_of_measure"] is None:
                raise ValueError("Null value in required field: unit")
            elif len(raw["unit_of_measure"]) > 16:
                raise ValueError("unit_of_measure exceeds max field length")
            else:
                unit = str(raw["unit_of_measure"])

            if raw["parameter_code"] is None:
                parameter_code = None
                print(f"parameter_code returned NULL for reading {reading_id}")
            elif len(raw["parameter_code"]) > 16:
                parameter_code = str(raw["parameter_code"])[:16]
                print(f"parameter_code exceeded max length, truncated for reading {reading_id}")
            else:
                parameter_code = str(raw["parameter_code"])

            if raw["statistic_id"] is None:
                statistic_id = None
                print(f"statistic_id returned NULL for reading {reading_id}")
            elif len(raw["statistic_id"]) > 16:
                statistic_id = str(raw["statistic_id"])[:16]
                print(f"statistic_id exceeded max length, truncated for reading {reading_id}")
            else:
                statistic_id = str(raw["statistic_id"])

            if raw["approval_status"] is None:
                approval_status = None
                print(f"approval_status returned NULL for reading {reading_id}")
            elif len(raw["approval_status"]) > 64:
                approval_status = str(raw["approval_status"])[:64]
                print(f"approval_status exceeded max length, truncated for reading {reading_id}")
            else:
                approval_status = str(raw["approval_status"])

            if raw["qualifier"] is None:
                qualifier = None
            elif len(raw["qualifier"]) > 255:
                qualifier = str(raw["qualifier"])[:255]
                print(f"qualifier exceeded max length, truncated for reading {reading_id}")
            else:
                qualifier = str(raw["qualifier"])

            if raw["last_modified"] is None:
                org_last_modified = None
                print(f"last_modified returned NULL for reading {reading_id}")
            else:
                org_last_modified = datetime.fromisoformat(raw["last_modified"])

            org_collecting = str(collecting_org) #Redundant step, since this is passed in as a parameter. I did this to maintain consistency.
            pull_source = str(api_endpoint) #Redundant step, since this is passed in as a parameter. I did this to maintain consistency.
            pull_time = start_time

        except (KeyError, ValueError, InvalidOperation) as e:
            print(f"skipping malformed reading: {e}")
            continue

        
        new_reading = {"reading_id" : reading_id,
                            "time_series_id" : time_series_id,
                            "monitor_location_id" : monitor_location_id,
                            "reading_time" : reading_time,
                            "value" : value,
                            "unit" : unit,
                            "parameter_code" : parameter_code,
                            "statistic_id" : statistic_id,
                            "approval_status" : approval_status,
                            "qualifier" : qualifier,
                            "org_last_modified" : org_last_modified,
                            "collecting_org" : org_collecting,
                            "pull_source" : pull_source,
                            "pull_time" : pull_time}
        return_items.append(new_reading)
    
    return_items_length = len(return_items)
    if return_items_length == 0:
        raise ValueError(f"GeoJSON at {api_endpoint} features failed to map to Dict structure correctly")

    print(f"Features Pulled: {features_length}\nRows ready for upload: {return_items_length}\nFailed Rows: {features_length-return_items_length}")

    return return_items
    

    



# Sample Data to test it with
monitor_id     = "USGS-03289500"
api_endpoint   = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/continuous/items"
api_endpoint_feature = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/continuous/items/USGS-03289500"
time_parameter = "P3M"

responses = usgs_pull_continuous(monitor_id, api_endpoint, time_parameter)
n = 0
for response in responses:
    n += 1
    # print(f"Generated response number: {n}")
    data = usgs_transform(response, api_endpoint, collecting_org="USGS")
    
