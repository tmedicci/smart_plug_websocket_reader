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

    print(dataPublished)
    
    if topicPublished == "/A207/datalogger/command":
        if dataPublished == 'q':
	    print("Disconecting")
	    client.disconnect()
    else:
        dataParsed = json.loads(dataPublished)
        #publish through mqtt
#        topic = "emon/sensor" + dataParsed["id"] + "/temperature"
#        client.publish(topic,dataParsed["measure"][0]["temp"]["data"])
#        print("publishing temperature = %s\n", dataParsed["measure"][0]["temp"]["data"])
    
        #publish through http request
        node_name = 'sensor' + dataParsed["id"]
        jsonurl = '{"temperature":' + str(dataParsed["measure"][0]["temp"]["data"]) + ','
        jsonurl = jsonurl + ' "humidity":' + str(dataParsed["measure"][1]["umidade"]["data"]) + ','
        jsonurl = jsonurl + ' "people":' + str(dataParsed["measure"][2]["people"]["data"]) + ','
        jsonurl = jsonurl + ' "door":' + str(dataParsed["measure"][3]["door"]["data"]) + '}'
        r = requests.get(
            'http://emonpi.local/emoncms/input/post',
            params={'node': node_name, 'fulljson': jsonurl, 'apikey': 'b1d1b91a22dffcb35338b32a978d54d6'}
        )
#        print(r.url)
########################################

broker_address="localhost"  #OK
#broker_address="raspberrypi.local"  #OK
#broker_address="rtsfgateway.local"
#broker_address="192.168.42.1"  #OK


# Definir nomes dos arquivos
arquivo1 = "sensor1_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".txt"
#fData = open(arquivo1, "a")
#fData.write("time,temperature,humidity\n")
#fData.close()

#dataParsedList = []

print("creating new instance")
client = mqtt.Client(arquivo1) #create new instance
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


#client.loop_start()
#print("Hit 'q' to exit")
#pressed_key = 0
#while pressed_key != 'q':
#    pressed_key = sys.stdin.read(1) # waits for charactere
#    if pressed_key == 'q':
#        print("Exit")
#    else:
#        print("Wrong option")
#        sys.stdin.read(1)       # reads the \n charactere
#
#client.loop_stop()
