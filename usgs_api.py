
import requests

def usgs_pull_continuous(monitor_id_inner, api_endpoint_inner, time_parameter_inner):
    print(f"Message from usgs_pull Continuous. monitor_id: {monitor_id_inner}, api_endpoint: {api_endpoint_inner}, time_parameter: {time_parameter_inner}")
    api_response = requests.get(api_endpoint_inner, params={"monitoring_location_"})




# Sample Data to test it with
monitor_id     = "USGS-03289500"
api_endpoint   = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/continuous/items"
time_parameter = "P9M"