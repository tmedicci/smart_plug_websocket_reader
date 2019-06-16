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
import csv
import subprocess
import logging.config
from collections import Counter

sendDeviceListCmd = "{\"MobileInternalIndex\":\"<random key>\",\"CommandType\":\"DeviceList\"}"
localTomada = "Time Energy"        

def setup_logging(
    default_path="Almond/WebSocketReader/websocket_logging.json",
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

def ensure_dir(filePath):
    directory = os.path.dirname(filePath)
    if not os.path.exists(directory):
        logger.info("Criando diretorio: %s", filePath)
        os.makedirs(directory)

def Check_Old_Files(fBasePathForTempFiles, fBasePathForUploadFiles, fUnixTimestamp, fDaysOffset, fLocalTomada):
    for dayOffset in range(fDaysOffset,0,-1):
        lastDayDate = (datetime.datetime.fromtimestamp(int(fUnixTimestamp))-datetime.timedelta(days=dayOffset)).strftime('%Y-%m-%d')
        lastDayFileName = lastDayDate+"_Peanuts_"+fLocalTomada+".day"
        logger.info("Procurando por arquivo do dia %s"%lastDayDate +": %s"%fBasePathForTempFiles+"/"+lastDayFileName)
        if(os.path.isfile(fBasePathForTempFiles+"/"+lastDayFileName)==True):
            logger.info("Arquivo do dia anterior encontrado:"+lastDayFileName)
            ensure_dir(fBasePathForUploadFiles+"/"+fLocalTomada+"/"+lastDayDate+"/Peanuts/")
            os.rename(fBasePathForTempFiles+"/"+lastDayFileName, fBasePathForUploadFiles+"/"+fLocalTomada+"/"+lastDayDate+"/Peanuts/"+lastDayFileName[:-4]+".csv")
            logger.info("Arquivo renomeado para:"+lastDayFileName[:-4]+".csv")
            #Envia o arquivo do dia anterior para o servidor
            try:
                cmdString = "/usr/local/bin/sshpass -p f7642151d13f0d081cd53d7d1b1 scp -r -o StrictHostKeyChecking=no "+fBasePathForUploadFiles+"/"+fLocalTomada+"/"+lastDayDate+"/ "+"root@138.197.86.155:/var/www/html/CPFL_3020/"+fLocalTomada+"/"
                output = subprocess.check_output(cmdString, shell=True)
                logger.info("Arquivo do dia %s enviado para o servidor com sucesso!" %lastDayDate)
            except subprocess.CalledProcessError as e:
                logger.error("Erro: Nao foi possivel enviar o arquivo ao servidor!")
        else:
            logger.info("Nao foi encontrado arquivo do dia %s" %lastDayDate)

def check_output_file(decodedMessage,
                        fDevicesIDsOnMessage,
                            unixTimestamp, 
                                fLocalTomada,
                                    fNumDevices,
                                        fDaysOffset):
    patternTimestamp = ('voltage', 'current', 'power', 'energy', 'apparent_power', 'reactive_power', 'power_factor')
    patternEmpty = ('',)
    devicesOnAlmond = {}
    devicesOnHeader = {}
    fLocalTomada = fLocalTomada.replace(" ","_")
    basePathForUploadFiles = "/home/pi/CPFL_3020"
    basePathForTempFiles = "/home/pi/CPFL_3020_TEMP"
    #gera o nome do arquivo .csv de acordo com o timestamp (unix) e o local da tomada
    
    actualDateTime = (datetime.datetime.fromtimestamp(int(unixTimestamp))).strftime('%Y-%m-%d')
    fileNameTemp = actualDateTime+"_Peanuts_"+fLocalTomada+".day"
        
    #Se o arquivo nao existir, cria o arquivo com as colunas padrao. Caso contrario, escreve os dados lidos
    if(os.path.isfile(basePathForTempFiles+"/"+fileNameTemp)==False):
        #Primeiramente, procura pelo arquivo .day referente aos dias anteriores
        Check_Old_Files(basePathForTempFiles, basePathForUploadFiles, unixTimestamp, fDaysOffset, fLocalTomada)
        #escreve o header do arquivo baseado no dia que foi criado e no numero de devices lido na mensagem (quando nao houver o arquivo anterior)
        ensure_dir(basePathForTempFiles+"/")
        with open(basePathForTempFiles+"/"+fileNameTemp, 'at', encoding="utf8") as csvfile:
            writer = csv.writer(csvfile, dialect='unix', quoting=csv.QUOTE_MINIMAL)
            headerRow = patternEmpty
            for i in list(decodedMessage['Devices'].keys()):
                deviceName = (decodedMessage['Devices'][i]['Data']['Name'])
                headerRow += (deviceName,) +patternEmpty*6
            logger.info("Header do arquivo: %s\n", headerRow)
            writer.writerow(headerRow)
            writer.writerow(("timestamp",)+ patternTimestamp*fNumDevices)   
    else:
        #Abre o arquivo para ler o header e contar o numero de devices nele
        with open(basePathForTempFiles+"/"+fileNameTemp, 'rt', encoding="utf8") as csvfile:
            reader = csv.reader(csvfile, dialect='unix')
            check_output_file.headerRow1 = next(reader)
            countHeaderDevices = sum([1 for elemt in list(Counter(check_output_file.headerRow1)) if elemt !=''])

            #Salva os nomes de devices no header e salva a posicao em um dicionario
            for i in range(1, countHeaderDevices*7, 7):
                deviceNameHeader = check_output_file.headerRow1[i]
                devicesOnHeader[deviceNameHeader] = i 

            #Salva tambem os nomes de devices da leitura e os IDs em um dicionario
            for i in list(decodedMessage['Devices'].keys()):
                deviceNameFromMessage = (decodedMessage['Devices'][i]['Data']['Name'])
                devicesOnAlmond[deviceNameFromMessage] = i 
                
            #Percorre os nomes dos devices provenientes da leitura para comparar com os devices do header
            for i in list(devicesOnAlmond.keys()):
                #Se nao houver o mesmo nome no header, cria um novo Header
                if (not(i in devicesOnHeader)):
                    logger.info("Novo device encontrado!")
                    newDeviceName = i
                    #Adiciona o padrao do header com o novo nome do device encontrado, mantendo os valores antigos
                    check_output_file.headerRow1 += (newDeviceName,) + patternEmpty*6
                    logger.info("Header atualizado: %s\n", check_output_file.headerRow1)
                    #Le a proxima linha do arquivo (referencias das colunas e adiciona novos valores para cada device adicionado)
                    check_output_file.headerRow2 = next(reader)
                    check_output_file.headerRow2 += patternTimestamp
                    #Cria um arquivo temporario (.temp) com as novas linhas de header e copia os valores obtidos anteriormente
                    with open(basePathForTempFiles+"/"+fileNameTemp+".temp", 'w+t', encoding="utf8") as csvfile:
                        writer = csv.writer(csvfile, dialect='unix', quoting=csv.QUOTE_MINIMAL)
                        logger.info("Novo arquivo criado com header atualizado!")
                        writer.writerow(check_output_file.headerRow1)
                        writer.writerow(check_output_file.headerRow2)
                        for row in reader:
                            writer.writerow(row)
                            
        #Se criou um arquivo temporario com um novo header, exclui o antigo e o renomeia
        if(os.path.isfile(basePathForTempFiles+"/"+fileNameTemp+".temp")==True):
            os.remove(basePathForTempFiles+"/"+fileNameTemp)
            os.rename(basePathForTempFiles+"/"+fileNameTemp+".temp", basePathForTempFiles+"/"+fileNameTemp)
            #Le o novo arquivo criado para extrair novamente as informacoes dos nomes disponiveis e salva em um dicionario
            with open(basePathForTempFiles+"/"+fileNameTemp, 'rt', encoding="utf8") as csvfile:
                reader = csv.reader(csvfile, dialect='unix')
                check_output_file.headerRow1 = next(reader)
                countHeaderDevices = sum([1 for elemt in list(Counter(check_output_file.headerRow1)) if elemt !=''])
                #Salva os nomes de devices no header e salva a posicao em um dicionario
                for i in range(1, countHeaderDevices*7, 7):
                    deviceNameHeader = check_output_file.headerRow1[i]
                    devicesOnHeader[deviceNameHeader] = i              

        #escreve os dados das tomadas no arquivo de saida
        with open(basePathForTempFiles+"/"+fileNameTemp, 'at', encoding="utf8") as csvfile:
            writer = csv.writer(csvfile, dialect='unix', quoting=csv.QUOTE_MINIMAL)
            row = ((unixTimestamp,))            
            #percorre os nomes no header do arquivo
            for i in range(1, countHeaderDevices*7, 7):
                deviceNameHeader = check_output_file.headerRow1[i]  
                #checa se existe o nome do header nos dispositivos relatados pelo Almond.
                if(deviceNameHeader in devicesOnAlmond.keys()):
                    #Se sim, checa se o nome esta na mensagem recebida: 
                    if(devicesOnAlmond[deviceNameHeader] in fDevicesIDsOnMessage):
                        #Se sim, escreve os dados no arquivo
                        logger.debug("Item encontrado na lista de Devices na mensagem: %s", devicesOnAlmond[deviceNameHeader])
                        row += (decodedMessage['Devices'][devicesOnAlmond[deviceNameHeader]]['DeviceValues']['12']['Value'],)
                        row += (decodedMessage['Devices'][devicesOnAlmond[deviceNameHeader]]['DeviceValues']['13']['Value'],)
                        row += (decodedMessage['Devices'][devicesOnAlmond[deviceNameHeader]]['DeviceValues']['11']['Value'],)
                        row += patternEmpty*4
                        logger.debug("Item removido da lista de Devices na mensagem: %s", devicesOnAlmond[deviceNameHeader])
                        fDevicesIDsOnMessage.remove(devicesOnAlmond[deviceNameHeader])
                    else:
                        #Se nao, escreve dados em branco
                        row += patternEmpty*7
                else:   
                    #Se nao, escreve dados em branco
                    row += patternEmpty*7
            #logger.info("Linha de dados: %s", row)
            logger.debug("Gravando linha de dados")
            writer.writerow(row)
check_output_file.headerRow1 = ()


def on_message(ws, message):
    global localTomada
    on_message.decoded = json.loads(message)
    #logger.debug("Recebeu mensagem")
    #Se a mensagem recebida for do tipo de atualizacao (automaticamente gerada), envia mensagem para recuperar dados de todas as tomadas. Caso contrario, le mensagem de todas as tomadas
    if on_message.decoded[u'CommandType']==u'DynamicIndexUpdated':
        logger.debug("Recebeu mensagem gerada pela tomada")
        deviceValueType = int(list(on_message.decoded['Devices'][list(on_message.decoded['Devices'].keys())[0]]['DeviceValues'])[0])
        #Se a mensagem for diferente da atualizacao de potencia ativa
        if(deviceValueType==11):
            logger.debug("Tipo da mensagem: potencia ativa")
            #checa se ja existe determinado timestamp no dicionario de IDs por timestamp
            unixTimestampFromRaspi = int(time.time())
            if(unixTimestampFromRaspi in on_message.acquireDevice):
                #se sim, adiciona ID a lista naquele timestamp
                logger.debug("Timestamp %s esta na lista de on_message.acquireDevice", str(unixTimestampFromRaspi))
                on_message.acquireDevice[unixTimestampFromRaspi].append(list(on_message.decoded['Devices'].keys())[0])
            else:
                #se nao, cria entrada com o timestamp
                logger.debug("Timestamp nao esta na lista de on_message.acquireDevice. Criada entrada: %s", str(unixTimestampFromRaspi))
                on_message.acquireDevice.update({unixTimestampFromRaspi:[list(on_message.decoded['Devices'].keys())[0]]})
            #se houver mais de uma entrada de timestamp no dicionario, envia entrada mensagem para ler devices
            logger.debug("Dicionario de timestamps e IDs: %s", str(on_message.acquireDevice))
            if(len(list(on_message.acquireDevice.keys()))>1):
                #if(on_message.minTimestamp != min(on_message.acquireDevice)):
                logger.debug("Enviou mensagem para ler a Device List")
                ws.send(sendDeviceListCmd)
                    #on_message.minTimestamp = min(on_message.acquireDevice)
    elif on_message.decoded[u'CommandType']==u'DeviceList':
        logger.debug("Tipo da mensagem: Device List")
        if(len(list(on_message.acquireDevice.keys()))>1):
            numberOfPeanutsDevices = len(list(on_message.decoded['Devices'].keys()))
            logger.debug("Gravando os IDs: %s", str(on_message.acquireDevice[min(on_message.acquireDevice.keys())]))
            check_output_file(on_message.decoded, on_message.acquireDevice[min(on_message.acquireDevice.keys())], min(on_message.acquireDevice.keys()), localTomada,numberOfPeanutsDevices, 5)
            logger.debug("Removendo entrada %s do dicionario", str(min(on_message.acquireDevice)))
            on_message.acquireDevice.pop(min(on_message.acquireDevice) ,None)
            logger.debug("Dicionario atualizado %s:", str(on_message.acquireDevice))
on_message.acquireDevice={}       
        
def on_error(ws, error):
    logger.error("Erro do websocket: %s",error)

def on_close(ws):
    logger.info("On close function:")
    
def on_open(ws):
    global localTomada
    logger.info("Conexao WebSocket aberta!")
    localTomada = localTomada.replace(" ","_")
    #on_message.minTimestamp=0

if __name__ == "__main__":
    websocket.enableTrace(False)
    setup_logging()
    logger = logging.getLogger(__name__)
    if len(sys.argv) < 3:
        logger.info("Uso incorreto. Insira os parametros de entrada: \"<webinterfaceUrl>:7681/<Login>/<password> <nome_do_local>\"")
        host = "ws://192.168.0.173:7681/admin/horde78"
        localTomada = "Time Energy"        
    else:
        host = sys.argv[1]
        localTomada = sys.argv[2]
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
