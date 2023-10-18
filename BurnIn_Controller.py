
# Imports
import sys
import argparse
import logging
import os
from datetime import datetime


import xml.etree.ElementTree as ET

from BurnIn_GUI import *


# Global variables
configDict = {}

def parseConfigParam(XMLName):	
	try:
		XMLtree = ET.parse(XMLName)
	except ET.ParseError as err:
		logger.warning("WARNING: Can't Parse XML file "+XMLName+". Using default config parameter.")
		logger.warning(err)
		return None
	logger.info("Parsing Configuration Parameter")
	
	XMLroot = XMLtree.getroot()
	for XMLchild in XMLroot:
		for XMLparam in  XMLchild:
			configDict[(XMLchild.tag,XMLparam.tag)]=XMLparam.text
			
# Main body
if __name__ == '__main__':



	parser = argparse.ArgumentParser()
	
	parser.add_argument("-d","--debug", help="Enable debug messages",  action='store_true')
	parser.add_argument("-x","--xml", help="XML configuration file")
	args=parser.parse_args()
	
	
	logger = logging.getLogger(__name__)
	
	now = datetime.now()
	LogName = now.strftime("Logs\BurnIn_controller_%Y_%m_%d_%H_%M_%S.log")
	
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
	
	# pars XML
	if args.xml:
		logger.info("XML Config file: " + str(args.xml))
		parseConfigParam(args.xml)
	else:
		if os.path.exists("config.xml"):
			logger.info("Using default XML Config file: config.xml" )
			parseConfigParam("config.xml")
		else:
			logger.info("XML Config file: " + str(args.xml))
		
	
	logger.debug("Configuration parameter")
	logger.debug(configDict)
	
	app = QtWidgets.QApplication(sys.argv)
	
	logger.debug("Opening GUI")
	
	BurnIn_app = BurnIn_GUI(configDict,logger)
	
	sys.exit(app.exec_())
	
