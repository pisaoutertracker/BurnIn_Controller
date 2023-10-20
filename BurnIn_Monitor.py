import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject
import time
from datetime import datetime

from MQTT_interface import *


class BurnIn_Monitor(QObject):

	def __init__(self,configDict,logger, MonitorTags, Julabo, FNALBox):
	
		super(BurnIn_Monitor,self).__init__();
		self.configDict=configDict
		self.logger = logger
		self.logger.info("MONITOR: Monitoring class initialized")
		
		self.MQTT =  MQTT_interface(configDict,logger)
		self.MonitorTags = MonitorTags
		self.Julabo = Julabo
		self.FNALBox = FNALBox

	def run(self):
		self.logger.info("MONITOR: Monitoring thread started")
		self.logger.info("MONITOR: Attempting first connection to MQTT server...")
		self.MQTT.connect()
		if self.MQTT.is_connected :
			self.MonitorTags[1].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
			self.MonitorTags[1].setText("Connected")
			
			
		while(1):
		
			self.MonitorTags[0].setStyleSheet("");
			self.MonitorTags[0].setText(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
			
			#MQTT cycle
			if (self.configDict.get(("MQTT","EnableMonitor"),"NOKEY").upper() == "TRUE"):
				if not self.MQTT.is_subscribed:
					self.logger.info("MONITOR: Attempting first connection to MQTT server...")
					self.MQTT.connect()
					if self.MQTT.is_connected :
						self.MonitorTags[1].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
						self.MonitorTags[1].setText("Connected")
				else:
					if self.MQTT.is_connected :
						self.MonitorTags[1].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
						self.MonitorTags[1].setText("Connected")
					else:
						self.MonitorTags[1].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ");
						self.MonitorTags[1].setText("Disconnected")
				
				self.MonitorTags[4].setText(self.MQTT.LastMessageTS)
				self.MonitorTags[5].setText(self.MQTT.LastMessage)
				self.MonitorTags[6].setText(self.MQTT.LastSource)
				
			#JULABO
			if (self.configDict.get(("Julabo","EnableMonitor"),"NOKEY").upper() == "TRUE"):
				self.Julabo.lock.acquire()
				if not self.Julabo.is_connected :
					self.Julabo.connect()
				if self.Julabo.is_connected :
					self.MonitorTags[2].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
					self.MonitorTags[2].setText("Connected")
					self.Julabo.sendTCP("status")
					self.MonitorTags[8].setText(self.Julabo.receive())
					self.Julabo.sendTCP("in_sp_00")
					self.MonitorTags[9].setText(self.Julabo.receive())
					self.MonitorTags[7].setText(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
				else:
					self.MonitorTags[2].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ");
					self.MonitorTags[2].setText("Disconnected")
				self.Julabo.lock.release()	
				
			#FNALBox
			if (self.configDict.get(("FNALBox","EnableMonitor"),"NOKEY").upper() == "TRUE"):
				self.FNALBox.lock.acquire()
				if not self.FNALBox.is_connected :
					self.FNALBox.connect()
				if self.FNALBox.is_connected :
					self.MonitorTags[3].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
					self.MonitorTags[3].setText("Connected")
					self.MonitorTags[10].setText(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
				else:
					self.MonitorTags[3].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ");
					self.MonitorTags[3].setText("Disconnected")
				self.FNALBox.lock.release()	
			
			self.logger.debug("MONITOR: Monitoring cycle done")
			time.sleep(3)