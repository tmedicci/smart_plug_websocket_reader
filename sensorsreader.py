###################################################
#
# This script is a datalogger script
#
# It subscribes to a mqtt topic where sensors data
# are published. It collects data and saves in a
# file.
# It also subscribes to another topic used to receive
# commands from outside the script. This is necessary
# because the script is intended to run in background.
#
# To run this script properly, use the following
# command in a terminal window:
#
# nohup python -u mqtt-client-parse.py > mqtt-parse.log &
#
# This command uses python to run the script in background.
# It also saves the script output to 'mqtt-parse.log'
# This command is based on the following web page:
# https://janakiev.com/til/python-background/
#
#
# Author: Murilo
# Date:
# Last modified: May, 9 2019
#
###################################################
import paho.mqtt.client as mqtt #import the client1
import time
import datetime
import sys
import json
import requests   # for http requests
############
def on_message(client, userdata, message):
    dataPublished = str(message.payload.decode("utf-8"))
    topicPublished = message.topic
    
    if topicPublished == "/A207/datalogger/command":
        if dataPublished == 'q':
            print("Disconecting")
            client.disconnect()
    else:
        dataParsed = json.loads(dataPublished)
    
        #publish through http request
        node_name = 'sensor-' + dataParsed["id"]
        jsonurl = '{"temperature":' + str(dataParsed["measure"][0]["temp"]["data"]) + ','
        jsonurl = jsonurl + ' "humidity":' + str(dataParsed["measure"][1]["umidade"]["data"]) + ','
        jsonurl = jsonurl + ' "people":' + str(dataParsed["measure"][2]["people"]["data"]) + ','
        jsonurl = jsonurl + ' "door":' + str(dataParsed["measure"][3]["door"]["data"]) + ','
        jsonurl = jsonurl + ' "door1":' + str(dataParsed["measure"][4]["door1"]["data"]) + '}'
        requests.get('http://rtsf-router.local/emoncms/input/post',
            params={'node': node_name, 'fulljson': jsonurl, 'apikey': '2a47b32ebfab41e5a17127c9cf2ac61f'}
        )

broker_address="localhost"  #OK

print("creating new instance")
client = mqtt.Client() #create new instance
client.on_message=on_message #attach function to callback

client.username_pw_set(username="emonpi",password="emonpimqtt2016")
print("connecting to broker: ",broker_address)
client.connect(broker_address, 1883, 60) #connect to broker
print("Subscribing to topic","/A207/+/measure")
client.subscribe("/A207/+/measure")
print("Subscribing to topic","/A207/datalogger/command")
client.subscribe("/A207/datalogger/command")

client.loop_forever()
print("Exiting")
