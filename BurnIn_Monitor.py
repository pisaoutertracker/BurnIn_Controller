import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject, pyqtSignal
import time
from datetime import datetime
import json
from __Constant import *

from MQTT_interface import *


class BurnIn_Monitor(QObject):

	Update_graph = pyqtSignal()
	#Update_manualOp_tab = pyqtSignal()

	def __init__(self,configDict,logger, SharedDict, Julabo, FNALBox, LVNames, HVNames):
	
		super(BurnIn_Monitor,self).__init__();
		self.configDict=configDict
		self.logger = logger
		self.logger.info("MONITOR: Monitoring class initialized")
		
		self.MQTT =  MQTT_interface(configDict,logger,"BurnIn_monitor")
		self.SharedDict = SharedDict
		self.SharedDict = SharedDict
		self.Julabo = Julabo
		self.FNALBox = FNALBox
		self.LVNames = LVNames
		self.HVNames = HVNames

		self.LastJulaboCycleDT = datetime.min
		self.LastFNALBoxCycleDT = datetime.min
		self.MQTT_JULABO_dict = {}
		self.MQTT_FNALBox_dict = {}

	def run(self):
		self.logger.info("MONITOR: Monitoring thread started")
		self.logger.info("MONITOR: Attempting first connection to MQTT server...")
		self.MQTT.connect()
		if self.MQTT.is_connected :
			self.SharedDict["MQTTMConn"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
			self.SharedDict["MQTTMConn"].setText("Connected")
			
		while(1):	
			if self.SharedDict["Quitting"]:
				return
		
			self.SharedDict["LastMonitor"].setStyleSheet("");
			self.SharedDict["LastMonitor"].setText(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
			
			#MQTT reception cycle
			if (self.configDict.get(("MQTT","EnableMonitor"),"NOKEY").upper() == "TRUE"):
				if not self.MQTT.is_subscribed:
					self.logger.info("MONITOR: Attempting first connection to MQTT server...")
					self.MQTT.connect()
					if self.MQTT.is_connected :
						self.SharedDict["MQTTMConn"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
						self.SharedDict["MQTTMConn"].setText("Connected")
				else:
					if self.MQTT.is_connected :
						self.SharedDict["MQTTMConn"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
						self.SharedDict["MQTTMConn"].setText("Connected")
					else:
						self.SharedDict["MQTTMConn"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ");
						self.SharedDict["MQTTMConn"].setText("Disconnected")
				
				if (self.MQTT.LastCAENMessageTS != "NEVER"):
					try:
						
						CAEN_dict = json.loads(self.MQTT.LastCAENMessage)
						self.SharedDict["HV_on"]=False
						self.SharedDict["LV_on"]=False
						for i in range (len(self.LVNames)):
							if self.LVNames[i]!="?":
								key = "caen_"+self.LVNames[i]+"_IsOn"
								if key in CAEN_dict:
									is_active = CAEN_dict[key]
									if is_active >0 :
										self.SharedDict["LastLV"+str((int)(i)).zfill(2)+"Status"].setText("ON")
										self.SharedDict["CAEN_table"].item(i,CTRLTABLE_LV_STAT_COL).setText("ON")
										self.SharedDict["CAEN_table"].item(i,CTRLTABLE_HV_NAME_COL).setBackground(QtGui.QColor("white"))
										self.SharedDict["LV_on"]=True
										
									else:
										self.SharedDict["LastLV"+str((int)(i)).zfill(2)+"Status"].setText("OFF")
										self.SharedDict["CAEN_table"].item(i,CTRLTABLE_LV_STAT_COL).setText("OFF")
										self.SharedDict["CAEN_table"].item(i,CTRLTABLE_HV_NAME_COL).setBackground(QtGui.QColor("lightgray"))	
								else:
									self.logger.warning("MONITOR: Status of LV channel "+ self.LVNames[i]+" not found in last MQTT message")
									
								key = "caen_"+self.LVNames[i]+"_VoltageCompliance"
								if (key) in CAEN_dict:
									self.SharedDict["LastLV"+str((int)(i)).zfill(2)+"VoltageSet"].setText(str(CAEN_dict[key]))
									self.SharedDict["CAEN_table"].item(i,CTRLTABLE_LV_VSET_COL).setText(str(CAEN_dict[key]))
								else:
									self.logger.warning("MONITOR: Voltage Compliance of LV channel "+ self.LVNames[i]+" not found in last MQTT message")

								key = "caen_"+self.LVNames[i]+"_Voltage"
								if (key) in CAEN_dict:
									self.SharedDict["LastLV"+str((int)(i)).zfill(2)+"Voltage"].setText(str(CAEN_dict[key]))
									self.SharedDict["CAEN_table"].item(i,CTRLTABLE_LV_VREAD_COL).setText(str(CAEN_dict[key]))
								else:
									self.logger.warning("MONITOR: Voltage of LV channel "+ self.LVNames[i]+" not found in last MQTT message")

								key = "caen_"+self.LVNames[i]+"_Current"
								if (key) in CAEN_dict:
									self.SharedDict["LastLV"+str((int)(i)).zfill(2)+"Current"].setText(str(CAEN_dict[key]))
									self.SharedDict["CAEN_table"].item(i,CTRLTABLE_LV_CURR_COL).setText(str(CAEN_dict[key]))
								else:
									self.logger.warning("MONITOR: Current of LV channel "+ self.LVNames[i]+" not found in last MQTT message")
							
							if self.HVNames[i]!="?":
								key = "caen_"+self.HVNames[i]+"_IsOn"
								if key in CAEN_dict:
									is_active = CAEN_dict[key]
									if is_active >0 :
										self.SharedDict["LastHV"+str((int)(i)).zfill(2)+"Status"].setText("ON")
										self.SharedDict["CAEN_table"].item(i,CTRLTABLE_HV_STAT_COL).setText("ON")
										self.SharedDict["CAEN_table"].item(i,CTRLTABLE_LV_NAME_COL).setBackground(QtGui.QColor("lightgrey"))
										self.SharedDict["HV_on"]=True
									else:
										self.SharedDict["LastHV"+str((int)(i)).zfill(2)+"Status"].setText("OFF")
										self.SharedDict["CAEN_table"].item(i,CTRLTABLE_HV_STAT_COL).setText("OFF")
										self.SharedDict["CAEN_table"].item(i,CTRLTABLE_LV_NAME_COL).setBackground(QtGui.QColor("white"))		
								else:
									self.logger.warning("MONITOR: Status of HV channel "+ self.HVNames[i]+" not found in last MQTT message")

								key = "caen_"+self.HVNames[i]+"_VoltageCompliance"
								if (key) in CAEN_dict:
									self.SharedDict["LastHV"+str((int)(i)).zfill(2)+"VoltageSet"].setText(str(CAEN_dict[key]))
									self.SharedDict["CAEN_table"].item(i,CTRLTABLE_HV_VSET_COL).setText(str(CAEN_dict[key]))
								else:
									self.logger.warning("MONITOR: Voltage of HV channel "+ self.HVNames[i]+" not found in last MQTT message")

								key = "caen_"+self.HVNames[i]+"_Voltage"
								if (key) in CAEN_dict:
									self.SharedDict["LastHV"+str((int)(i)).zfill(2)+"Voltage"].setText(str(CAEN_dict[key]))
									self.SharedDict["CAEN_table"].item(i,CTRLTABLE_HV_VREAD_COL).setText(str(CAEN_dict[key]))
								else:
									self.logger.warning("MONITOR: Voltage of HV channel "+ self.HVNames[i]+" not found in last MQTT message")

								key = "caen_"+self.HVNames[i]+"_Current"
								if (key) in CAEN_dict:
									self.SharedDict["LastHV"+str((int)(i)).zfill(2)+"Current"].setText(str(CAEN_dict[key]))
									self.SharedDict["CAEN_table"].item(i,CTRLTABLE_HV_CURR_COL).setText(str(CAEN_dict[key]))
								else:
									self.logger.warning("MONITOR: Current of HV channel "+ self.HVNames[i]+" not found in last MQTT message")

					
						self.SharedDict["LastMQTTCAENMsgTS"].setText(self.MQTT.LastCAENMessageTS)
						deltaSec = (datetime.now()-self.MQTT.LastCAENMessageDT).total_seconds()
						if (deltaSec < MONITOR_UPDATE_LIMIT):
							self.SharedDict["CAEN_updated"] = True
							self.SharedDict["LastMQTTCAENMsgTS"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ")
						else:
							self.SharedDict["CAEN_updated"] = False
							self.SharedDict["LastMQTTCAENMsgTS"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ")
							

					except Exception as e:
						self.logger.warning("MONITOR: error splitting MQTT CAEN message. Details below.")
						self.logger.error(e)
				
				if (self.MQTT.LastM5MessageTS != "NEVER"):

					try:
						
						M5_dict = json.loads(self.MQTT.LastM5Message)

						self.SharedDict["LastM5DP"].setText(str(M5_dict["dewpoint"]))
						self.SharedDict["Ctrl_ExtDewPoint"].setText(str(M5_dict["dewpoint"]))
						self.SharedDict["LastM5Temp"].setText(str(M5_dict["temperature"]))
						self.SharedDict["LastM5Humi"].setText(str(M5_dict["RH"]))
						self.SharedDict["LastM5Pres"].setText(str(M5_dict["Pressure"]))
					
						self.SharedDict["LastMQTTM5MsgTS"].setText(self.MQTT.LastM5MessageTS)
						deltaSec = (datetime.now()-self.MQTT.LastM5MessageDT).total_seconds()
						if deltaSec < MONITOR_UPDATE_LIMIT:
							self.SharedDict["M5_updated"] = True
							self.SharedDict["LastMQTTM5MsgTS"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ")
						else:
							self.SharedDict["M5_updated"] = False
							self.SharedDict["LastMQTTM5MsgTS"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ")

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
					self.SharedDict["JULABOConn"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
					self.SharedDict["JULABOConn"].setText("Connected")
					self.Julabo.sendTCP("status")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.SharedDict["LastJulaboStatus"].setText(reply)
						self.MQTT_JULABO_dict["status"]=reply
						if self.SharedDict["LastJulaboStatus"].text().find("START")!=-1:
							self.SharedDict["Ctrl_StatusJulabo"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
							self.SharedDict["Ctrl_StatusJulabo"].setText(self.SharedDict["LastJulaboStatus"].text())
						else:
							self.SharedDict["Ctrl_StatusJulabo"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ");
							self.SharedDict["Ctrl_StatusJulabo"].setText(self.SharedDict["LastJulaboStatus"].text())
					else:
						self.JulaboCycleOK = False
							
							
						
						
					self.Julabo.sendTCP("in_sp_00")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.SharedDict["LastJulaboSP1"].setText(reply.replace(" ", ""))
						self.SharedDict["Ctrl_Sp1"].setText(self.SharedDict["LastJulaboSP1"].text())
						self.MQTT_JULABO_dict["Temp_SP1"]=float(reply.replace(" ", ""))
					else:
						self.JulaboCycleOK = False
						
					self.Julabo.sendTCP("in_sp_01")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.SharedDict["LastJulaboSP2"].setText(reply.replace(" ", ""))
						self.SharedDict["Ctrl_Sp2"].setText(self.SharedDict["LastJulaboSP2"].text())
						self.MQTT_JULABO_dict["Temp_SP2"]=float(reply.replace(" ", ""))
					else:
						self.JulaboCycleOK = False
						
					self.Julabo.sendTCP("in_sp_02")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.SharedDict["LastJulaboSP3"].setText(reply.replace(" ", ""))
						self.SharedDict["Ctrl_Sp3"].setText(self.SharedDict["LastJulaboSP3"].text())
						self.MQTT_JULABO_dict["Temp_SP3"]=float(reply.replace(" ", ""))
					else:
						self.JulaboCycleOK = False
						
					self.Julabo.sendTCP("in_pv_00")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.SharedDict["LastJulaboBT"].setText(reply.replace(" ", ""))
						self.MQTT_JULABO_dict["Temp_bath"]=float(reply.replace(" ", ""))
					else:
						self.JulaboCycleOK = False
						
					self.Julabo.sendTCP("in_pv_01")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.SharedDict["LastJulaboHP"].setText(reply.replace(" ", ""))
						self.MQTT_JULABO_dict["HP"]=float(reply.replace(" ", ""))
					else:
						self.JulaboCycleOK = False
						
					self.Julabo.sendTCP("in_mode_01")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						Sp = str(int(reply.replace(" ", ""))+1)
						self.SharedDict["LastJulaboTSP"].setText(Sp)
						self.SharedDict["Ctrl_TSp"].setText(Sp)
						self.MQTT_JULABO_dict["target_SP"]=float(reply.replace(" ", ""))
					else:
						self.JulaboCycleOK = False
						
					if self.SharedDict["LastJulaboTSP"].text()[:1]=="1":
						self.SharedDict["Ctrl_TargetTemp"].setText(self.SharedDict["LastJulaboSP1"].text())
					elif self.SharedDict["LastJulaboTSP"].text()[:1]=="2":
						self.SharedDict["Ctrl_TargetTemp"].setText(self.SharedDict["LastJulaboSP2"].text())
					elif self.SharedDict["LastJulaboTSP"].text()[:1]=="3":
						self.SharedDict["Ctrl_TargetTemp"].setText(self.SharedDict["LastJulaboSP3"].text())
							
						
				else:
					self.SharedDict["JULABOConn"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ");
					self.SharedDict["JULABOConn"].setText("Disconnected")
					self.JulaboCycleOK = False
				self.Julabo.lock.release()
				
				if self.JulaboCycleOK:
					self.LastJulaboCycleDT = datetime.now()
					self.SharedDict["LastJulaboMsgTS"].setText(self.LastJulaboCycleDT.strftime("%d/%m/%Y %H:%M:%S"))
					if self.MQTT.is_connected:
						self.MQTT.publish("/julabo/full",json.dumps(self.MQTT_JULABO_dict))
				if (datetime.now()-self.LastJulaboCycleDT).total_seconds() < MONITOR_UPDATE_LIMIT:
					self.SharedDict["LastJulaboMsgTS"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ")
					self.SharedDict["Julabo_updated"] = True
				else:
					self.SharedDict["LastJulaboMsgTS"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ")
					self.SharedDict["Julabo_updated"] = False
					
					
					

					
				
			#FNALBox
			if (self.configDict.get(("FNALBox","EnableMonitor"),"NOKEY").upper() == "TRUE"):
				self.logger.debug("MONITOR: FNAL lock requested")
				self.FNALBox.lock.acquire()
				self.logger.debug("MONITOR: FNAL lock acquired")
				self.FNALBoxCycleOK = True
				if not self.FNALBox.is_connected :
					self.FNALBox.connect()
				if self.FNALBox.is_connected :
					self.SharedDict["FNALConn"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
					self.SharedDict["FNALConn"].setText("Connected")
					self.FNALBox.sendTCP("[10]")
					reply = self.FNALBox.receive()
					if (reply != "None" and reply != "TCP error"):
						reply_list = reply[1:-1].split(",")
						try:
							self.SharedDict["LastFNALBoxTemp0"].setText(reply_list[FNAL_T0_OFFSET])
							self.MQTT_FNALBox_dict["Temp0"]=float(reply_list[FNAL_T0_OFFSET])
							self.SharedDict["LastFNALBoxTemp1"].setText(reply_list[FNAL_T1_OFFSET][1:])
							self.MQTT_FNALBox_dict["Temp1"]=float(reply_list[FNAL_T1_OFFSET][1:])
							
							self.SharedDict["LastFNALBoxDoor"].setText(reply_list[FNAL_RS_OFFSET][1:])
							self.MQTT_FNALBox_dict["Door"]=float(reply_list[FNAL_RS_OFFSET][1:])
							if float(reply_list[FNAL_RS_OFFSET][1:]) > FNAL_RS_THR:
								self.SharedDict["Ctrl_StatusDoor"].setText("OPEN")
							else:
								self.SharedDict["Ctrl_StatusDoor"].setText("CLOSED")
                                
							for i in range(NUM_BI_SLOTS):
								self.SharedDict["LastFNALBoxOW"+str(i)].setText(reply_list[i+FNAL_OW_OFFSET][1:])
								self.MQTT_FNALBox_dict["OW"+str((int)(i+1)).zfill(2)]=float(reply_list[i+FNAL_OW_OFFSET][1:])
							self.MQTT_FNALBox_dict["DewPoint"]=float(reply_list[FNAL_DP_OFFSET][1:])
							self.SharedDict["LastFNALBoxDP"].setText(reply_list[FNAL_DP_OFFSET][1:])
							self.SharedDict["Ctrl_IntDewPoint"].setText(reply_list[FNAL_DP_OFFSET][1:])
							
							IntTemp_arr = [float(self.SharedDict["LastFNALBoxTemp1"].text()),float(self.SharedDict["LastFNALBoxTemp0"].text())]
							for i in range (NUM_BI_SLOTS):
								IntTemp_arr.append(float(self.SharedDict["LastFNALBoxOW"+str(i)].text())) 
							self.SharedDict["Ctrl_LowerTemp"] = min(IntTemp_arr)
							self.SharedDict["Ctrl_HigherTemp"] = max(list(filter(MAX_VALID_TEMP.__gt__,IntTemp_arr)))
						except Exception as e:
							self.logger.warning("MONITOR: error splitting FNAL reply "+reply)
							self.FNALBoxCycleOK = False
					self.SharedDict["LastFNALBoxMsgTS"].setText(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
				else:
					self.FNALBoxCycleOK = False
					self.SharedDict["FNALConn"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ")
					self.SharedDict["FNALConn"].setText("Disconnected")
				self.FNALBox.lock.release()
				self.logger.debug("MONITOR: FNAL lock released")	
				
				if self.FNALBoxCycleOK:
					self.LastFNALBoxCycleDT = datetime.now()
					self.SharedDict["LastFNALBoxMsgTS"].setText(self.LastFNALBoxCycleDT.strftime("%d/%m/%Y %H:%M:%S"))
					if self.MQTT.is_connected:
						self.MQTT_FNALBox_dict["StatusLock"]=self.SharedDict["Ctrl_StatusLock"].text()
						self.MQTT_FNALBox_dict["AirFlow"]=self.SharedDict["Ctrl_StatusFlow"].text()
						self.MQTT.publish("/fnalbox/full",json.dumps(self.MQTT_FNALBox_dict))						
				if (datetime.now()-self.LastFNALBoxCycleDT).total_seconds() < MONITOR_UPDATE_LIMIT:
					self.SharedDict["LastFNALBoxMsgTS"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ")
					self.SharedDict["FNALBox_updated"] = True
				else:
					self.SharedDict["LastFNALBoxMsgTS"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ")
					self.SharedDict["FNALBox_updated"] = False
					
					
					
			if self.JulaboCycleOK and self.FNALBoxCycleOK and self.SharedDict["BI_Active"]:
				self.SharedDict["Time_arr"].append(time.time())
				self.SharedDict["DewPoint_arr"].append(float(self.SharedDict["Ctrl_IntDewPoint"].text()))
				self.SharedDict["Temp_arr"].append(float(self.SharedDict["LastFNALBoxTemp0"].text()))
				
				if self.SharedDict["BI_TestActive"]:
					self.SharedDict["TimeTest_arr"].append(time.time())
					self.SharedDict["TempTest_arr"].append(float(self.SharedDict["LastFNALBoxTemp0"].text()))
					
				
				try:
					self.SharedDict["Targ_arr"].append(float(self.SharedDict["Ctrl_TargetTemp"].text()))
				except Exception as e:
					self.SharedDict["Targ_arr"].append(0.0)
					self.logger.error(e)
				self.Update_graph.emit()
			
			#self.Update_manualOp_tab.emit()
			self.logger.debug("MONITOR: Monitoring cycle done")
			time.sleep(MONITOR_SLEEP)
