import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject
import time

from MQTT_interface import *


class BurnIn_Monitor(QObject):

	def __init__(self,configDict,logger):
	
		super(BurnIn_Monitor,self).__init__();
		self.configDict=configDict
		self.logger = logger
		self.logger.info("Monitoring class initialized")
		
		self.MQTT =  MQTT_interface(configDict,logger)

	def run(self):
		self.logger.info("Monitoring thread started")
		self.MQTT.connect()
		
		while(1):
			self.logger.debug("Monitoring cycle done")
			time.sleep(1)
		