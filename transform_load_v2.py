# This is version 2
# Final version of transform and load version
# It contains a core function that transform data and load to bigquery with sends Slack notification

# import libraries
import os
import json

import requests
from datetime import datetime
import pytz
from google.cloud import storage
from google.cloud import bigquery


# config variables class
class Config:
    # get bucket name from environment variables
    raw_bucket_name = os.environ.get("RAW_BUCKET_NAME")
    transformed_bucket_name = os.environ.get("TRANSFORMED_BUCKET_NAME")
    # get table id from environment variables
    saimai_table = os.environ.get("TABLE_ID_SAIMAI")
    pathumwan_table = os.environ.get("TABLE_ID_PATHUMWAN")
    # get slack webhook url from environment variables
    slack_url = os.environ.get("SLACK_URL")

    # Thai timezone
    thai_tz = pytz.timezone("Asia/Bangkok")


# define list filenames in Cloud Storage function
# docs => https://cloud.google.com/storage/docs/listing-objects
def list_file_in_gcs():
    storage_client = storage.Client()
    # specify folder
    blobs = storage_client.list_blobs(Config.raw_bucket_name, prefix="processing/", delimiter="/")
    
    # return filenames list
    return [blob.name for blob in blobs]


# define load json file from Cloud Storage to memory of Cloud Function function
# docs => https://cloud.google.com/storage/docs/downloading-objects-into-memory
def load_json_to_memory(file_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(Config.raw_bucket_name)

    blob = bucket.blob(file_name)
    raw_data_bytes = blob.download_as_string()
    raw_data = raw_data_bytes.decode("utf-8")
    
    return json.loads(raw_data)


# define convert unix time to datetime object
def convert_time(unix_time):
    return datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")


# define transform data function
def transform_data(raw_data):
    # empty result dictionary
    result_dict = {}

    # time list in raw data
    time_list = ["dt", "sunrise", "sunset"]
    # if available in raw data
    uncertain_list = ["wind_gust", "rain"]

    # for loop every district
    for district in raw_data:
        # empty temporary dictionary
        temp_dict = {}

        # for loop weather and air quality data
        for key in raw_data[district]:
            # if it is weather data
            if key == "weather":
                # for loop to transform
                for i in raw_data[district][key]["current"]:
                    # if key is in time list
                    if i in time_list:
                        # call convert_time function and append to temporary dictionary
                        temp_dict[i] = convert_time(raw_data[district][key]["current"][i])
                    # if key is not in time list, uncertain list, and weather
                    elif i not in (time_list + uncertain_list + ["weather"]):
                        # append to temporary dictionary
                        temp_dict[i] = raw_data[district][key]["current"][i]
                    # if key is in uncertain list
                    elif i in uncertain_list:
                        # append to temporary dictionary
                        temp_dict[i] = raw_data[district][key]["current"][i]
                    # else - key is in weather
                    else:
                        # for loop to append to temporary dictionary
                        for j in raw_data[district][key]["current"]["weather"][0]:
                            temp_dict[j] = raw_data[district][key]["current"]["weather"][0][j]
            # else - air quality data
            else:
                # append aqi data to temporary dictionary
                temp_dict["aqi"] = raw_data[district][key]["list"][0]["main"]["aqi"]
                # for loop to append components data to temporary dictionary
                for i in raw_data[district][key]["list"][0]["components"]:
                    temp_dict[i] = raw_data[district][key]["list"][0]["components"][i]

        # append each district data to result dictionary    
        result_dict[district] = temp_dict

    # return result dictionary
    return result_dict


# define transformed data (backup) to Cloud Storage
# docs => https://cloud.google.com/storage/docs/uploading-objects-from-memory
def backup_to_storage(file_name, result_dict):
    storage_client = storage.Client()
    bucket = storage_client.bucket(Config.transformed_bucket_name)

    # convert result dictionary to json
    json_data = json.dumps(result_dict)

    blob = bucket.blob(file_name)
    blob.upload_from_string(json_data)


# define insert data to BigQuery function
# docs => https://cloud.google.com/bigquery/docs/streaming-data-into-bigquery
def insert_to_bigquery(result_dict):
    client = bigquery.Client()

    # for loop to every district in transformed data
    for district in result_dict:
        # if transformed data is Saimai district
        if district == "saimai_data":
            # get Saimai district transformed data
            row_to_insert = [result_dict["saimai_data"]]
            # insert to Saimai table
            client.insert_rows_json(Config.saimai_table, row_to_insert, row_ids=[None] * len(row_to_insert))
        # if transformed data is Pathumwan data
        elif district == "pathumwan_data":
            # get Pathumwan district transformed data
            row_to_insert = [result_dict["pathumwan_data"]]
            # insert to Pathumwan table
            client.insert_rows_json(Config.pathumwan_table, row_to_insert, row_ids=[None] * len(row_to_insert))


# define move raw data file from processing folder to processed folder (copy then delete)
# docs => https://cloud.google.com/storage/docs/copying-renaming-moving-objects
def move_raw_data_to_processed(file_name):
    storage_client = storage.Client()
    source_bucket = storage_client.bucket(Config.raw_bucket_name)
    source_blob = source_bucket.blob(file_name)
    destination_bucket = storage_client.bucket(Config.raw_bucket_name)
    # specify destination folder (processed folder)
    destination_blob_name = "processed/" + file_name.split("/")[-1]

    destination_generation_match_precondition = 0

    blob_copy = source_bucket.copy_blob(
        source_blob, destination_bucket, destination_blob_name, if_generation_match=destination_generation_match_precondition,
    )
    source_bucket.delete_blob(file_name)


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
    print("The transform and load function has run.")

    # try this section
    try:
        # list raw data filenames
        raw_data_file_name = list_file_in_gcs()

        # for loop in every raw data filenames
        for file_name in raw_data_file_name:
            # if filename end with json
            if file_name.split(".")[-1] == "json":
                # load raw data to memory
                raw_data = load_json_to_memory(file_name)
                # transform data
                result_dict = transform_data(raw_data)

                # get current datetime
                current_date = datetime.now(Config.thai_tz).strftime("%Y%m%d_%H%M%S")
                # backup transformed data to Cloud Storage
                backup_to_storage(f"transformed_data_{current_date}.json", result_dict)

                # insert transformed data to BigQuery
                insert_to_bigquery(result_dict)

                # move raw data from processing folder to processed folder
                move_raw_data_to_processed(file_name)
        
                # send slack notification
                slack_notification("Transformed and loaded data successfully.")

        # print message to logs
        print("The transform and load function has run successfully")

    # except the function has an error
    except:
        # send slack notification
        slack_notification("The pipeline has an error in TRANSFORM & LOAD part!")

        # print message to logs
        print("The transform and load function has an error.")
