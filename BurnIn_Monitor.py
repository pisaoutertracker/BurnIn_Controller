import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject
import time
from datetime import datetime
import json

from MQTT_interface import *


class BurnIn_Monitor(QObject):

	def __init__(self,configDict,logger, MonitorTags, Julabo, FNALBox, LVNames, HVNames):
	
		super(BurnIn_Monitor,self).__init__();
		self.configDict=configDict
		self.logger = logger
		self.logger.info("MONITOR: Monitoring class initialized")
		
		self.MQTT =  MQTT_interface(configDict,logger)
		self.MonitorTags = MonitorTags
		self.MonitorTags = MonitorTags
		self.Julabo = Julabo
		self.FNALBox = FNALBox
		self.LVNames = LVNames
		self.HVNames = HVNames

		self.LastJulaboCycleDT = datetime.min
		self.LastFNALBoxCycleDT = datetime.min

	def run(self):
		self.logger.info("MONITOR: Monitoring thread started")
		self.logger.info("MONITOR: Attempting first connection to MQTT server...")
		self.MQTT.connect()
		if self.MQTT.is_connected :
			self.MonitorTags["MQTTConn"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
			self.MonitorTags["MQTTConn"].setText("Connected")
			
		while(1):		
		
			self.MonitorTags["LastMonitor"].setStyleSheet("");
			self.MonitorTags["LastMonitor"].setText(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
			
			#MQTT cycle
			if (self.configDict.get(("MQTT","EnableMonitor"),"NOKEY").upper() == "TRUE"):
				if not self.MQTT.is_subscribed:
					self.logger.info("MONITOR: Attempting first connection to MQTT server...")
					self.MQTT.connect()
					if self.MQTT.is_connected :
						self.MonitorTags["MQTTConn"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
						self.MonitorTags["MQTTConn"].setText("Connected")
				else:
					if self.MQTT.is_connected :
						self.MonitorTags["MQTTConn"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
						self.MonitorTags["MQTTConn"].setText("Connected")
					else:
						self.MonitorTags["MQTTConn"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ");
						self.MonitorTags["MQTTConn"].setText("Disconnected")
				
				if (self.MQTT.LastCAENMessageTS != "NEVER"):
					try:
						
						CAEN_dict = json.loads(self.MQTT.LastCAENMessage)
						for i in range (len(self.LVNames)):
							if self.LVNames[i]!="?":
								key = "caen_"+self.LVNames[i]+"_IsOn"
								if key in CAEN_dict:
									is_active = CAEN_dict[key]
									if is_active >0 :
										self.MonitorTags["LastLV"+str((int)(i)).zfill(2)+"Status"].setText("ON")
									else:
										self.MonitorTags["LastLV"+str((int)(i)).zfill(2)+"Status"].setText("OFF")	
								else:
									self.logger.warning("MONITOR: Status of LV channel "+ self.LVNames[i]+" not found in last MQTT message")

								key = "caen_"+self.LVNames[i]+"_Voltage"
								if (key) in CAEN_dict:
									self.MonitorTags["LastLV"+str((int)(i)).zfill(2)+"Voltage"].setText(str(CAEN_dict[key]))
								else:
									self.logger.warning("MONITOR: Voltage of LV channel "+ self.LVNames[i]+" not found in last MQTT message")

								key = "caen_"+self.LVNames[i]+"_Current"
								if (key) in CAEN_dict:
									self.MonitorTags["LastLV"+str((int)(i)).zfill(2)+"Current"].setText(str(CAEN_dict[key]))
								else:
									self.logger.warning("MONITOR: Current of LV channel "+ self.LVNames[i]+" not found in last MQTT message")
							
							if self.HVNames[i]!="?":
								key = "caen_"+self.HVNames[i]+"_IsOn"
								if key in CAEN_dict:
									is_active = CAEN_dict[key]
									if is_active >0 :
										self.MonitorTags["LastHV"+str((int)(i)).zfill(2)+"Status"].setText("ON")
									else:
										self.MonitorTags["LastHV"+str((int)(i)).zfill(2)+"Status"].setText("OFF")	
								else:
									self.logger.warning("MONITOR: Status of HV channel "+ self.HVNames[i]+" not found in last MQTT message")

								key = "caen_"+self.HVNames[i]+"_Voltage"
								if (key) in CAEN_dict:
									self.MonitorTags["LastHV"+str((int)(i)).zfill(2)+"Voltage"].setText(str(CAEN_dict[key]))
								else:
									self.logger.warning("MONITOR: Voltage of HV channel "+ self.HVNames[i]+" not found in last MQTT message")

								key = "caen_"+self.HVNames[i]+"_Current"
								if (key) in CAEN_dict:
									self.MonitorTags["LastHV"+str((int)(i)).zfill(2)+"Current"].setText(str(CAEN_dict[key]))
								else:
									self.logger.warning("MONITOR: Current of HV channel "+ self.HVNames[i]+" not found in last MQTT message")

					
						self.MonitorTags["LastMQTTCAENMsgTS"].setText(self.MQTT.LastCAENMessageTS)
						deltaSec = (datetime.now()-self.MQTT.LastCAENMessageDT).total_seconds()
						if (deltaSec < 60):
							self.MonitorTags["CAEN_updated"] = True
							self.MonitorTags["LastMQTTCAENMsgTS"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ")
						else:
							self.MonitorTags["CAEN_updated"] = False
							self.MonitorTags["LastMQTTCAENMsgTS"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ")
							

					except Exception as e:
						self.logger.warning("MONITOR: error splitting MQTT CAEN message. Details below.")
						self.logger.error(e)
				
				if (self.MQTT.LastM5MessageTS != "NEVER"):

					try:
						
						M5_dict = json.loads(self.MQTT.LastM5Message)

						self.MonitorTags["LastM5DP"].setText(str(M5_dict["dewpoint"]))
						self.MonitorTags["Ctrl_ExtDewPoint"].setText(str(M5_dict["dewpoint"]))
						self.MonitorTags["LastM5Temp"].setText(str(M5_dict["temperature"]))
						self.MonitorTags["LastM5Humi"].setText(str(M5_dict["RH"]))
						self.MonitorTags["LastM5Pres"].setText(str(M5_dict["Pressure"]))
					
						self.MonitorTags["LastMQTTM5MsgTS"].setText(self.MQTT.LastM5MessageTS)
						deltaSec = (datetime.now()-self.MQTT.LastM5MessageDT).total_seconds()
						if deltaSec < 60:
							self.MonitorTags["M5_updated"] = True
							self.MonitorTags["LastMQTTM5MsgTS"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ")
						else:
							self.MonitorTags["M5_updated"] = False
							self.MonitorTags["LastMQTTM5MsgTS"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ")

					except Exception as e:
						self.logger.warning("MONITOR: error splitting MQTT M5 message. Details below.")
						self.logger.error(e)
						
			#JULABO
			if (self.configDict.get(("Julabo","EnableMonitor"),"NOKEY").upper() == "TRUE"):
				self.Julabo.lock.acquire()
				self.JulaboCycleOK = True
				if not self.Julabo.is_connected :
					self.Julabo.connect()
				if self.Julabo.is_connected :
					self.MonitorTags["JULABOConn"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
					self.MonitorTags["JULABOConn"].setText("Connected")
					self.Julabo.sendTCP("status")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.MonitorTags["LastJulaboStatus"].setText(reply)
						if self.MonitorTags["LastJulaboStatus"].text().find("START")!=-1:
							self.MonitorTags["Ctrl_StatusJulabo"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
							self.MonitorTags["Ctrl_StatusJulabo"].setText(self.MonitorTags["LastJulaboStatus"].text())
						else:
							self.MonitorTags["Ctrl_StatusJulabo"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ");
							self.MonitorTags["Ctrl_StatusJulabo"].setText(self.MonitorTags["LastJulaboStatus"].text())
					else:
						self.JulaboCycleOK = False
							
							
						
						
					self.Julabo.sendTCP("in_sp_00")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.MonitorTags["LastJulaboSP1"].setText(reply.replace(" ", ""))
						self.MonitorTags["Ctrl_Sp1"].setText(self.MonitorTags["LastJulaboSP1"].text())
					else:
						self.JulaboCycleOK = False
						
					self.Julabo.sendTCP("in_sp_01")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.MonitorTags["LastJulaboSP2"].setText(reply.replace(" ", ""))
						self.MonitorTags["Ctrl_Sp2"].setText(self.MonitorTags["LastJulaboSP2"].text())
					else:
						self.JulaboCycleOK = False
						
					self.Julabo.sendTCP("in_sp_02")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.MonitorTags["LastJulaboSP3"].setText(reply.replace(" ", ""))
						self.MonitorTags["Ctrl_Sp3"].setText(self.MonitorTags["LastJulaboSP3"].text())
					else:
						self.JulaboCycleOK = False
						
					self.Julabo.sendTCP("in_pv_00")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.MonitorTags["LastJulaboBT"].setText(reply.replace(" ", ""))
					else:
						self.JulaboCycleOK = False
						
					self.Julabo.sendTCP("in_pv_01")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.MonitorTags["LastJulaboHP"].setText(reply.replace(" ", ""))
					else:
						self.JulaboCycleOK = False
						
					self.Julabo.sendTCP("in_mode_01")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						Sp = str(int(reply.replace(" ", ""))+1)
						self.MonitorTags["LastJulaboTSP"].setText(Sp)
						self.MonitorTags["Ctrl_TSp"].setText(Sp)
					else:
						self.JulaboCycleOK = False
						
					if self.MonitorTags["LastJulaboTSP"].text()[:1]=="1":
						self.MonitorTags["Ctrl_TargetTemp"].setText(self.MonitorTags["LastJulaboSP1"].text())
					elif self.MonitorTags["LastJulaboTSP"].text()[:1]=="2":
						self.MonitorTags["Ctrl_TargetTemp"].setText(self.MonitorTags["LastJulaboSP2"].text())
					elif self.MonitorTags["LastJulaboTSP"].text()[:1]=="3":
						self.MonitorTags["Ctrl_TargetTemp"].setText(self.MonitorTags["LastJulaboSP3"].text())
							
						
				else:
					self.MonitorTags["JULABOConn"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ");
					self.MonitorTags["JULABOConn"].setText("Disconnected")
					self.JulaboCycleOK = False
				self.Julabo.lock.release()
				
				if self.JulaboCycleOK:
					self.LastJulaboCycleDT = datetime.now()
					self.MonitorTags["LastJulaboMsgTS"].setText(self.LastJulaboCycleDT.strftime("%d/%m/%Y %H:%M:%S"))
				if (datetime.now()-self.LastJulaboCycleDT).total_seconds() < 60:
					self.MonitorTags["LastJulaboMsgTS"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ")
					self.MonitorTags["Julabo_updated"] = True
				else:
					self.MonitorTags["LastJulaboMsgTS"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ")
					self.MonitorTags["Julabo_updated"] = False
					
					
					

					
				
			#FNALBox
			if (self.configDict.get(("FNALBox","EnableMonitor"),"NOKEY").upper() == "TRUE"):
				self.logger.debug("MONITOR: FNAL lock requested")
				self.FNALBox.lock.acquire()
				self.logger.debug("MONITOR: FNAL lock acquired")
				self.FNALBoxCycleOK = True
				if not self.FNALBox.is_connected :
					self.FNALBox.connect()
				if self.FNALBox.is_connected :
					self.MonitorTags["FNALConn"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
					self.MonitorTags["FNALConn"].setText("Connected")
					self.FNALBox.sendTCP("[10]")
					time.sleep(0.250)
					reply = self.FNALBox.receive()
					if (reply != "None" and reply != "TCP error"):
						reply_list = reply[1:-1].split(",")
						try:
							self.MonitorTags["LastFNALBoxTemp0"].setText(reply_list[0])
							self.MonitorTags["LastFNALBoxTemp1"].setText(reply_list[1][1:])
							self.MonitorTags["LastFNALBoxDP"].setText(reply_list[14][1:])
							self.MonitorTags["Ctrl_IntDewPoint"].setText(reply_list[14][1:])
						except Exception as e:
							self.logger.warning("MONITOR: error splitting FNAL reply "+reply)
							self.FNALBoxCycleOK = False
					self.MonitorTags["LastFNALBoxMsgTS"].setText(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
				else:
					self.FNALBoxCycleOK = False
					self.MonitorTags["FNALConn"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ");
					self.MonitorTags["FNALConn"].setText("Disconnected")
				self.FNALBox.lock.release()
				self.logger.debug("MONITOR: FNAL lock released")	
				
				if self.FNALBoxCycleOK:
					self.LastFNALBoxCycleDT = datetime.now()
					self.MonitorTags["LastFNALBoxMsgTS"].setText(self.LastFNALBoxCycleDT.strftime("%d/%m/%Y %H:%M:%S"))
				if (datetime.now()-self.LastFNALBoxCycleDT).total_seconds() < 60:
					self.MonitorTags["LastFNALBoxMsgTS"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ")
					self.MonitorTags["FNALBox_updated"] = True
				else:
					self.MonitorTags["LastFNALBoxMsgTS"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ")
					self.MonitorTags["FNALBox_updated"] = False
			
			self.logger.debug("MONITOR: Monitoring cycle done")
			time.sleep(3)
