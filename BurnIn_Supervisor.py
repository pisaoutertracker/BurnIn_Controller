import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject, pyqtSignal
import time
from datetime import datetime
import json
from __Constant import *

from MQTT_interface import *


class BurnIn_Supervisor(QObject):


	def __init__(self,configDict,logger, SharedDict):
	
		super(BurnIn_Supervisor,self).__init__();
		self.configDict=configDict
		self.logger = logger
		self.logger.info("SUPERVISOR: Supervisor class initialized")
		
		self.MQTT =  MQTT_interface(configDict,logger,"BurnIn_supervisor")
		self.SharedDict = SharedDict

	def run(self):
		self.logger.info("SUPERVISOR: SUPERVISOR thread started...waiting "+ str(SUPERVISOR_START_DELAY) +"s")
		time.sleep(SUPERVISOR_START_DELAY)
		self.logger.info("SUPERVISOR: SUPERVISOR is now armed")
		self.logger.info("SUPERVISOR: Attempting first connection to MQTT server...")
		self.MQTT.connect()
		if self.MQTT.is_connected :
			self.SharedDict["MQTTConn"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
			self.SharedDict["MQTTConn"].setText("Connected")
			
		while(1):	

			
	
			self.logger.debug("SUPERVISOR: SUPERVISOR cycle done")
			time.sleep(SUPERVISOR_SLEEP)
