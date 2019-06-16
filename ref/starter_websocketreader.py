# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

import sys
import re
import subprocess
import logging.config
import os.path
import json

def setup_logging(
    default_path="/home/pi/Almond/WebSocketReader/starter_websocketreader_logging.json",
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

#Procura um processo pelo nome em ps
def find_this_process(process_name):
  ps = subprocess.Popen("ps -eaf | grep "+process_name, shell=True, stdout=subprocess.PIPE)
  output = ps.stdout.read()
  ps.stdout.close()
  ps.wait()
  
  return str(output)

#Checa se o processo esta ativo
def is_this_process_running(path_of_process, process_name):
  output = find_this_process(process_name)
  #print(str(output))

  if re.search(path_of_process+process_name, output) is None:
    #print("Nao ha processo de [%s] rodando" %process_name)
    return False
  else:
    #print("Processo de %s ja em execucao" %process_name)
    return True

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    setup_logging()
    if len(sys.argv) <4:
        logger.error("Uso incorreto do parametro de entrada. Por favor, use: \"sudo python3 starter_websocketreader.py [caminho_do_script_.py/] [websocketreader.py] [<webinterfaceUrl>:7681/<Login>/<password>] [<nome_do_local>]\"")
    else:
        if(is_this_process_running(sys.argv[1], sys.argv[2])==False):
            logger.info("Processo nao esta em execucao. Startando %s! ..." %sys.argv[2])
            script = sys.argv[1]+sys.argv[2]
            logger.info("string: %s", script)
            try: 
                subprocess.Popen(['sudo', 'python3', script, sys.argv[3], sys.argv[4]])
            except:
                logger.error("Nao foi possivel iniciar o processo. Verifique o nome do mesmo.")
        else:
            logger.info("Processo ja em execucao.")
