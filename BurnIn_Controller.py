# Imports
import sys
import argparse
import logging
import os, platform
from datetime import datetime
import yaml


import xml.etree.ElementTree as ET

from BurnIn_GUI import *

# Global variables
configDict = {}

def parseYamlParam(yaml_parser):
    logger.info("Parsing Configuration Parameter")
    for classKey, classDict in yaml_parser.items():
        for paramKey , value in  classDict.items():
            configDict[(classKey,paramKey)]=value
            
# Main body
if __name__ == '__main__':



    parser = argparse.ArgumentParser()
    
    parser.add_argument("-d","--debug", help="Enable debug messages",  action='store_true')
    parser.add_argument("-y","--yaml", help="YAML configuration file")
    args=parser.parse_args()
    

    
    logger = logging.getLogger(__name__)
    
    now = datetime.now()
    
    LogDir = "Logs"
    if not os.path.exists(LogDir):
        os.makedirs(LogDir)

    if platform.system()=="Windows":
        LogName = now.strftime("Logs\BurnIn_controller_%Y_%m_%d_%H_%M_%S.log")
    else:
        LogName = now.strftime("Logs/BurnIn_controller_%Y_%m_%d_%H_%M_%S.log")

    
    if args.debug:
        logging.basicConfig( format="%(asctime)s | %(name)s | %(levelname)s : %(message)s",datefmt="%Y-%m-%dT%H:%M:%S%z",
        level=logging.DEBUG, handlers=[
        logging.FileHandler(LogName),
        logging.StreamHandler()
    ]) # ISO-8601 timestamp
        logging.debug("Debugging messages activated")
    else:
        logging.basicConfig( format="%(asctime)s | %(levelname)s : %(message)s",datefmt="%Y-%m-%dT%H:%M:%S%z",
        level=logging.INFO, handlers=[
        logging.FileHandler(LogName),
        logging.StreamHandler()]) # ISO-8601 timestamp
    
    
    logger.info("BURN IN controller started")
    
    # pars YAML
    if args.yaml:
        logger.info("YAML Config file: " + str(args.yaml))
        with open(args.yaml, 'r') as file:
            prime_service = yaml.safe_load(file)
            parseYamlParam(prime_service)
    else:
        if os.path.exists("Config.yaml"):
            logger.info("Using default YAML Config file: Config.yaml" )
            with open("Config.yaml", 'r') as file:
                prime_service = yaml.safe_load(file)
                parseYamlParam(prime_service)
        else:
            logger.info("YAML Config file: " + str(args.yaml))
            
        
    
    logger.info("Configuration parameter")
    logger.info(configDict)
    
    app = QtWidgets.QApplication(sys.argv)
    
    logger.debug("Opening GUI")
    
    BurnIn_app = BurnIn_GUI(configDict,logger)
    exit_code=app.exec()
    BurnIn_app.QuitThreads()
    
    logger.info("GUI closed: exit code "+str(exit_code))
    sys.exit(exit_code)
    
