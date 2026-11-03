
import requests

from collections.abc import Iterator
import requests
import json

def usgs_pull_continuous(monitor_id_inner: str, api_endpoint_inner: str, time_parameter_inner: str):
    # print(f"Message from usgs_pull Continuous. monitor_id: {monitor_id_inner}, api_endpoint: {api_endpoint_inner}, time_parameter: {time_parameter_inner}")
    try:
        usgs_params = {"time" : time_parameter_inner, 
                    "limit" : 10000,
                    "monitoring_location_id" : monitor_id_inner
                    }
        response = requests.get(api_endpoint_inner, params=usgs_params, timeout=30)
        response.raise_for_status()

        yield response
        next_url = None
        for link in response.json()["links"]:
            if link["rel"] == "next":
                next_url = link["href"]

        while next_url != None:
            response = requests.get(next_url, timeout=30)
            response.raise_for_status()
            yield response
            next_url = None
            for link in response.json()["links"]:
                    if link["rel"] == "next":
                        next_url = link["href"]
    except requests.exceptions.HTTPError as e:
         raise requests.exceptions.RequestException(f"Pull failed for monitor {monitor_id_inner} from {api_endpoint_inner}: {e}") from e

    except requests.exceptions.Timeout as e:
         raise requests.exceptions.Timeout(f"Pull failed for monitor {monitor_id_inner} from {api_endpoint_inner}: {e}") from e



    

    

    



# Sample Data to test it with
monitor_id     = "USGS-03289500"
api_endpoint   = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/continuous/items"
api_endpoint_feature = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/continuous/items/USGS-03289500"
time_parameter = "P9M"

responses = usgs_pull_continuous(monitor_id, api_endpoint, time_parameter)
n = 0
for response in responses:
    n += 1
    print(f"Generated response number: {n}")
