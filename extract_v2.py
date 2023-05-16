# This is version 2
# Final version of extract version
# It contains a core function that fetches data from API and sends Slack notification function

# import libraries
import os
import json

import requests
from datetime import datetime
import pytz
from google.cloud import storage


# config variables class
class Config:
    # get API KEY from environment variable
    api_key = os.environ.get("API_KEY")
    # get bucket name from environment variable
    bucket_name = os.environ.get("BUCKET_NAME")
    # get slack webhook url from environment variable
    slack_url = os.environ.get("SLACK_URL")

    # thai timezone
    thai_tz = pytz.timezone("Asia/Bangkok")
    # parts that unnecessary from API
    parts = "minutely,hourly,daily,alerts"
    # system of units
    units = "metric"


# define get data from API function
def get_data(lat, lon):
    # weather data API url
    weather_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude={Config.parts}&units={Config.units}&appid={Config.api_key}"
    # air quality API url
    air_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={Config.api_key}"

    # get a message payload from API
    weather_response = requests.get(weather_url)
    air_response = requests.get(air_url)

    # get dictionary result
    weather_result = weather_response.json()
    air_result = air_response.json()

    # return dictionary result
    return weather_result, air_result


# define upload raw data to cloud storage function
# docs => https://cloud.google.com/storage/docs/uploading-objects-from-memory
def upload_to_storage(file_name, data):
    storage_client = storage.Client()
    bucket = storage_client.bucket(Config.bucket_name)

    # convert result dictionary to json
    json_data = json.dumps(data)

    # specify folder - processing (waiting for transforming)
    blob = bucket.blob(f"processing/{file_name}")
    blob.upload_from_string(json_data)


# define send message notification to Slack function
def slack_notification(message):
    # convert message to json
    data = json.dumps({"text": message})
    # headers of post requests
    headers = {"Content-Type": "application/json"}
    # post message to slack
    requests.post(url=Config.slack_url, data=data, headers=headers)


# define main function to entry run
def main(event, context):
    # print message to logs
    print("The extract function has run.")

    # try this section
    try:
        # coordinates of Saimai district and Pathumwan district
        coor = {
            "saimai": {"lat": "13.896", "lon": "100.672"},
            "pathumwan": {"lat": "13.740", "lon": "100.535"}
        }

        # empty result dictionary
        result_dict = {}

        # for loop to get data from API
        for district in coor:
            lat = coor[district]["lat"]
            lon = coor[district]["lon"]

            # get weather data and air quality data
            weather_data, air_data = get_data(lat, lon)

            # append result to the result dictionary
            result_dict[f"{district}_data"] = {"weather": weather_data, "air": air_data}

        # get current datetime
        current_date = datetime.now(Config.thai_tz).strftime("%Y%m%d_%H%M%S")

        # upload result to Cloud Storage
        upload_to_storage(f"raw_data_{current_date}.json", result_dict)

        # send slack notification
        slack_notification("Extracted data from OpenWeather API succesfully.")

        # print message to logs
        print("The extracted function has run successfully.")

    # except the function has an error
    except:
        # send slack notification
        slack_notification("The pipeline has an error in EXTRACT function!")

        # print message to logs
        print("The extracted function has an error")
