import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject
import time
from datetime import datetime

from MQTT_interface import *


class BurnIn_Monitor(QObject):

	def __init__(self,configDict,logger, MonitorInfo, Julabo, FNALBox):
	
		super(BurnIn_Monitor,self).__init__();
		self.configDict=configDict
		self.logger = logger
		self.logger.info("MONITOR: Monitoring class initialized")
		
		self.MQTT =  MQTT_interface(configDict,logger)
		self.MonitorInfo = MonitorInfo
		self.Julabo = Julabo
		self.FNALBox = FNALBox

	def run(self):
		self.logger.info("MONITOR: Monitoring thread started")
		self.logger.info("MONITOR: Attempting first connection to MQTT server...")
		self.MQTT.connect()
		if self.MQTT.is_connected :
			self.MonitorInfo["MQTTConn"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
			self.MonitorInfo["MQTTConn"].setText("Connected")
			
			
		while(1):
		
			self.MonitorInfo["LastMonitor"].setStyleSheet("");
			self.MonitorInfo["LastMonitor"].setText(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
			
			#MQTT cycle
			if (self.configDict.get(("MQTT","EnableMonitor"),"NOKEY").upper() == "TRUE"):
				if not self.MQTT.is_subscribed:
					self.logger.info("MONITOR: Attempting first connection to MQTT server...")
					self.MQTT.connect()
					if self.MQTT.is_connected :
						self.MonitorInfo["MQTTConn"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
						self.MonitorInfo["MQTTConn"].setText("Connected")
				else:
					if self.MQTT.is_connected :
						self.MonitorInfo["MQTTConn"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
						self.MonitorInfo["MQTTConn"].setText("Connected")
					else:
						self.MonitorInfo["MQTTConn"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ");
						self.MonitorInfo["MQTTConn"].setText("Disconnected")
				
				if (self.MQTT.LastCAENMessageTS != "NEVER"):
					self.MonitorInfo["LastMQTTCAENMsgTS"].setText(self.MQTT.LastCAENMessageTS)
					try:
						MQTT_splitted = self.MQTT.LastCAENMessage[1:-1].split(",")
						for idx in range(0,len(MQTT_splitted),3):
							MQTT_splitted[idx].replace(" ", "")
							MQTT_splitted[idx+1].replace(" ", "")
							MQTT_splitted[idx+2].replace(" ", "")
							if idx<28:
								self.MonitorInfo["CH"+str((int)(idx/3)).zfill(2)+"_ID"].setText(MQTT_splitted[idx].split("_")[1].replace(" ", ""))
								is_active = float(MQTT_splitted[idx].split(":")[1])
								if is_active >0 :
									self.MonitorInfo["CH"+str((int)(idx/3)).zfill(2)+"_ST"].setText("ON")
								else:
									self.MonitorInfo["CH"+str((int)(idx/3)).zfill(2)+"_ST"].setText("OFF")
									
								self.MonitorInfo["CH"+str((int)(idx/3)).zfill(2)+"_V"].setText(MQTT_splitted[idx+1].split(":")[1].replace(" ", ""))
								self.MonitorInfo["CH"+str((int)(idx/3)).zfill(2)+"_I"].setText(MQTT_splitted[idx+2].split(":")[1].replace(" ", ""))
									
							else:
								self.logger.warning("MONITOR: too many channel in MQTT CAEN message!")
					except Exception as e:
						self.logger.warning("MONITOR: error splitting MQTT CAEN message. Details below.")
						self.logger.error(e)
				
				if (self.MQTT.LastM5MessageTS != "NEVER"):
					self.MonitorInfo["LastMQTTM5MsgTS"].setText(self.MQTT.LastM5MessageTS)
					try:
						MQTT_splitted = self.MQTT.LastM5Message[1:-1].replace(" ", "").split(",")
						self.MonitorInfo["LastM5DP"].setText(MQTT_splitted[0].split(":")[1])
						self.MonitorInfo["LastM5Temp"].setText(MQTT_splitted[1].split(":")[1])
						self.MonitorInfo["LastM5Humi"].setText(MQTT_splitted[2].split(":")[1])
						self.MonitorInfo["LastM5Pres"].setText(MQTT_splitted[3].split(":")[1])
					except Exception as e:
						self.logger.warning("MONITOR: error splitting MQTT M5 message. Details below.")
						self.logger.error(e)
						
			#JULABO
			if (self.configDict.get(("Julabo","EnableMonitor"),"NOKEY").upper() == "TRUE"):
				self.Julabo.lock.acquire()
				if not self.Julabo.is_connected :
					self.Julabo.connect()
				if self.Julabo.is_connected :
					self.MonitorInfo["JULABOConn"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
					self.MonitorInfo["JULABOConn"].setText("Connected")
					self.Julabo.sendTCP("status")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.MonitorInfo["LastJulaboStatus"].setText(reply)
						
					self.Julabo.sendTCP("in_sp_00")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.MonitorInfo["LastJulaboSP1"].setText(reply)
						
					self.Julabo.sendTCP("in_sp_01")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.MonitorInfo["LastJulaboSP2"].setText(reply)
						
					self.Julabo.sendTCP("in_sp_02")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.MonitorInfo["LastJulaboSP3"].setText(reply)
						
					self.Julabo.sendTCP("in_pv_00")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.MonitorInfo["LastJulaboBT"].setText(reply)
						
					self.Julabo.sendTCP("in_pv_01")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.MonitorInfo["LastJulaboHP"].setText(reply)
						
					self.Julabo.sendTCP("in_mode_01")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.MonitorInfo["LastJulaboTSP"].setText(reply)
						
					self.MonitorInfo["LastJulaboMsgTS"].setText(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
				else:
					self.MonitorInfo["JULABOConn"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ");
					self.MonitorInfo["JULABOConn"].setText("Disconnected")
				self.Julabo.lock.release()	
				
			#FNALBox
			if (self.configDict.get(("FNALBox","EnableMonitor"),"NOKEY").upper() == "TRUE"):
				self.FNALBox.lock.acquire()
				if not self.FNALBox.is_connected :
					self.FNALBox.connect()
				if self.FNALBox.is_connected :
					self.MonitorInfo["FNALConn"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
					self.MonitorInfo["FNALConn"].setText("Connected")
					self.FNALBox.sendTCP("[10]")
					reply = self.FNALBox.receive()
					if (reply != "None" and reply != "TCP error"):
						reply_list = reply[1:-1].split(",")
						try:
							self.MonitorInfo["LastFNALBoxTemp0"].setText(reply_list[0])
							self.MonitorInfo["LastFNALBoxTemp1"].setText(reply_list[1][1:])
							self.MonitorInfo["LastFNALBoxDP"].setText(reply_list[14][1:])
						except Exception as e:
							self.logger.warning("MONITOR: error splitting FNAL reply "+reply)
					self.MonitorInfo["LastFNALBoxMsgTS"].setText(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
				else:
					self.MonitorInfo["FNALConn"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ");
					self.MonitorInfo["FNALConn"].setText("Disconnected")
				self.FNALBox.lock.release()	
			
			self.logger.debug("MONITOR: Monitoring cycle done")
			time.sleep(3)