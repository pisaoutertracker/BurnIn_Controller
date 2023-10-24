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
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.MonitorTags[8].setText(reply)
					self.Julabo.sendTCP("in_sp_00")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.MonitorTags[9].setText(reply)
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
					self.FNALBox.sendTCP("[10]")
					reply = self.FNALBox.receive()
					if (reply != "None" and reply != "TCP error"):
						reply_list = reply[1:-1].split(",")
						try:
							self.MonitorTags[11].setText(reply_list[0])
							self.MonitorTags[12].setText(reply_list[1][1:])
							self.MonitorTags[13].setText(reply_list[2][1:])
							self.MonitorTags[14].setText(reply_list[3][1:])
							self.MonitorTags[15].setText(reply_list[14][1:])
						except Exception as e:
							self.logger.warning("MONITOR: error splitting FNAL reply "+reply)
					self.MonitorTags[10].setText(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
				else:
					self.MonitorTags[3].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ");
					self.MonitorTags[3].setText("Disconnected")
				self.FNALBox.lock.release()	
			
			self.logger.debug("MONITOR: Monitoring cycle done")
			time.sleep(3)