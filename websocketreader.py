# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

import sys
import websocket
import threading
import time
import json
import string
import os.path
import datetime
import subprocess
import http.client
import urllib.parse
import logging.config
from collections import Counter

def setup_logging(
    default_path="somewhere",
    default_level=logging.INFO,
    env_key="LOG_CFG"
):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

def on_message(ws, message):
    on_message.decoded = json.loads(message)
    if on_message.decoded[u'type']==u'loadPackets':
        logger.info("Recebeu mensagem de loadPackets gerada pela Smart Plug")
        timezoneOffset = int(on_message.decoded[u'timezoneOffset'])
        logger.debug("Offset da Timezone: " + str(timezoneOffset))
        logger.debug("Recebeu mensagem de loadPackets gerada pela tomada:")
        meterData = on_message.decoded[u'meterData']
        orderedMeterData = sorted(meterData, key = lambda k:k['timestampUtc'])
        for item in orderedMeterData:
            logger.debug("timestamp: " + str(item['timestampUtc']))
            logger.debug("pot. ativa: " + str(int(item['potenciaAtiva'])/100))
            logger.debug("pot. reativa: " + str(int(item['potenciaReativa'])/100))
            logger.debug("tensão: " + str(int(item['tensao'])/100))
            params = urllib.parse.urlencode({'time': item['timestampUtc'], 'node': 'smartplug-' + str(localTomada), 'apikey': str(apiKey),'data': str(item)})
            headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
            conn = http.client.HTTPConnection("rtsf-router.local", 80)
            conn.request("POST", "/emoncms/input/post/", params, headers)
            r1 = conn.getresponse()
            logger.debug("request status: " + str(r1.status) + ". Request reason: " + str(r1.reason) + ". Request response data: " + str(r1.read()))    
        
def on_error(ws, error):
    logger.error("Erro do websocket: %s",error)

def on_close(ws):
    logger.info("On close function:")
    
def on_open(ws):
    global localTomada
    logger.info("Conexao WebSocket aberta!")
    
if __name__ == "__main__":
    websocket.enableTrace(False)
    setup_logging()
    logger = logging.getLogger(__name__)
    if len(sys.argv) < 4:
        logger.error("Uso incorreto. Insira os parametros de entrada: \"<webinterfaceUrl> <nome_do_local> <api_write_key-emoncms>\"")
    else:
        host = sys.argv[1]
        localTomada = sys.argv[2]
        apiKey = sys.argv[3]
        try:
            while True:
                ws = websocket.WebSocketApp(host,
                                on_message = on_message,
                                on_error = on_error,
                                on_close = on_close)
                ws.on_open = on_open
                ws.run_forever(ping_interval=3, ping_timeout=2)
                time.sleep(5)    
        except:
            logger.error("O programa foi interrompido definitivamente")
