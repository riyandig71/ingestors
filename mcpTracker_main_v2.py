from google.cloud import pubsub
import datetime
import requests
import pytz
import json
import time
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="/app/application_default_credentials.json"
#os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="/home/kali/iot-projects/ioh-stp/ingestor-sm/application_default_credentials.json"

os.environ.setdefault("GCLOUD_PROJECT", "ioh-simulator")

#from google.oauth2 import service_account

#credentials = service_account.Credentials.from_service_account_file("/home/kali/iot-projects/ioh-stp/ingestor-sm/application_default_credentials.json")
#client = language.LanguageServiceClient(credentials=credentials)

# Imports the Cloud Logging client library
import google.cloud.logging

# Instantiates a client
clientlog = google.cloud.logging.Client()

# Retrieves a Cloud Logging handler based on the environment
# you're running in and integrates the handler with the
# Python logging module. By default this captures all logs
# at INFO level and higher
clientlog.setup_logging()

import logging

def publish_pubsub(project_id,topic_id, msg):
    publisher = pubsub.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    data_str = json.dumps(msg,separators=(',',':'))
    # Data must be a bytestring
    data = data_str.encode("utf-8")
    # When you publish a message, the client returns a future.
    future = publisher.publish(topic_path, data)

    print(future.result())
    print(f"Published messages to {topic_path}.")
    return future.result()
    
def stream_data(url):
    # Get the URL
    global last_data
    response = requests.get(url)

    status = response.json()['DEVICE']['STATUS']
    command = response.json()['DEVICE']['COMMAND']
    ndata = response.json()['DEVICE']['NDATA']
    
    time_local = response.json()['DEVICE']['DATA'][0]['TIME']
    local = pytz.timezone('Asia/Jakarta')
    naive = datetime.datetime.strptime(time_local,"%Y-%m-%d %H:%M:%S")
    local_dt = local.localize(naive, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    timestamp = int(round(utc_dt.timestamp()*1000))
    
    imei = response.json()['DEVICE']['DATA'][0]['IMEI']
    name = response.json()['DEVICE']['DATA'][0]['NAME']
    longitude = response.json()['DEVICE']['DATA'][0]['LONGITUDE']
    latitude = response.json()['DEVICE']['DATA'][0]['LATITUDE']
    speed = response.json()['DEVICE']['DATA'][0]['SPEED']
    heading = response.json()['DEVICE']['DATA'][0]['HEADING']
    moving = response.json()['DEVICE']['DATA'][0]['MOVING']

    if moving == "0":
        moving = False
    else:
        moving = True

    battery = response.json()['DEVICE']['DATA'][0]['BATTERY']
    main_voltage = response.json()['DEVICE']['DATA'][0]['MAIN_VOLTAGE']
    gsm_signal = response.json()['DEVICE']['DATA'][0]['GSM_SIGNAL']
    address = response.json()['DEVICE']['DATA'][0]['ADDRESS']

    mylist = {
            "type" : "inboundDataEventMsg", 
            "networkId" : "tracker-fmc130-netw-dummy1", 
            "deviceId" : str(imei)+'-dummy1', #macId
            "aliasKey" : "imei",
            "data": [
                { "path" : "status", "value" : status},
                { "path" : "command", "value" : command},
                { "path" : "ndata", "value" : ndata},
                { "path" : "data/time", "value" : timestamp},
                { "path" : "data/imei", "value" : str(imei)+'-dummy1'},
                { "path" : "data/position/lat", "value" : float(latitude)},
                { "path" : "data/position/lon", "value" : float(longitude)},
                { "path" : "data/speed", "value" : speed},
                { "path" : "data/heading", "value" : heading},
                { "path" : "data/moving", "value" : moving},
                { "path" : "data/battery", "value" : battery},
                { "path" : "data/main_voltage", "value" : main_voltage},
                { "path" : "data/gsm_signal", "value" : gsm_signal},
                { "path" : "data/address", "value" : address},
            ]}

    project_id = 'ioh-simulator'
    topic_id = 'default-processor'


    if (last_data == None) or (last_data['DEVICE']['DATA'][0]['IMEI'] == imei and last_data['DEVICE']['DATA'][0]['TIME'] != time_local):
        msgID = publish_pubsub(project_id,topic_id, mylist)
        last_data = response.json()
        logging.info(json.dumps(response.json()))

last_data = None

try:
    while True:
        stream_data("https://mamigo.id/api/realtime/63f0a743e1e121845a4967c85f571dde")
        time.sleep(10)

except KeyboardInterrupt:
    print("exiting")
    client.disconnect()
    client.loop_stop()
