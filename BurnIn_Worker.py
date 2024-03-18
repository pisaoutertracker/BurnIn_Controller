import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
import time
from datetime import datetime
import subprocess
from __Constant import *
import json




## Class implementation for the Worker module of the GUI controller.
#
#  The worker is a inheriting from pyQt library in order to create assign slots and signals
class BurnIn_Worker(QObject):

	Request_msg = pyqtSignal(str,str)
	Request_confirm_sig = pyqtSignal(str)
	Request_input_dsb = pyqtSignal(str,float,float,float)
	BI_terminated = pyqtSignal()
	
	BI_Update_GUI_sig = pyqtSignal(dict)
	BI_Clear_Monitor_sig = pyqtSignal()

	## Init function.
	def __init__(self,configDict,logger, SharedDict, Julabo, FNALBox, CAENController, DB_interface):

	
		super(BurnIn_Worker,self).__init__();
		self.configDict=configDict
		self.logger = logger
		self.Julabo = Julabo
		self.FNALBox = FNALBox
		self.DB_interface = DB_interface
		self.CAENController = CAENController
		self.SharedDict = SharedDict
		
		self.logger.info("Worker class initialized")
		self.last_op_ok= True
		
		
	#################################################################
	## Basic functions. directly called from "Test Operation tab"
	#################################################################
	
	## Function to send a cmd string to the Julabo interface
	# implemented as a is a Pyqt slot
	# NOT executed if:
	# - TCP socket is not connected and connection attempt fails
	# Control on cmd execution: none
	@pyqtSlot(str)
	def SendJulaboCmd(self,cmd):
		self.Julabo.lock.acquire()
		self.logger.info("Sending Julabo cmd "+cmd)
		if not self.Julabo.is_connected :
			self.Julabo.connect()
		if self.Julabo.is_connected :
			self.Julabo.sendTCP(cmd)
			self.logger.info(self.Julabo.receive())
		else:	
			self.last_op_ok= False	
		self.Julabo.lock.release()
		
	## Function to send a cmd string to the CAEN controller interface
	# implemented as a is a Pyqt slot
	# NOT executed if:
	# - TCP socket is not connected and connection attempt fails	
	# Control on cmd execution: none
	@pyqtSlot(str)
	def SendCAENControllerCmd(self,cmd):
		self.CAENController.lock.acquire()
		self.logger.info("Sending CAENController cmd "+cmd)
		if not self.CAENController.is_connected :
			self.CAENController.connect()
		if self.CAENController.is_connected :
			self.CAENController.sendTCP(cmd)
			time.sleep(CAEN_SLEEP_AFTER_TCP)
			self.logger.info(self.CAENController.receive())
			self.CAENController.close()
		else:	
			self.last_op_ok= False	
		self.CAENController.lock.release()
	

	## Function to send a cmd string to the Julabo interface
	# implemented as a is a Pyqt slot
	# NOT executed if:
	# - TCP socket is not connected and connection attempt fails	
	# Control on cmd execution: none
	@pyqtSlot(str)
	def SendFNALBoxCmd(self,cmd):
		self.logger.info("WORKER: Requesting lock on FNALBox")
		self.FNALBox.lock.acquire()
		self.logger.info("Sending FNALBox cmd "+cmd)
		if not self.FNALBox.is_connected :
			self.FNALBox.connect()
		if self.FNALBox.is_connected :
			self.FNALBox.sendTCP(cmd)
			time.sleep(FNAL_SLEEP_AFTER_TCP)
			self.logger.info(self.FNALBox.receive())
		else:	
			self.last_op_ok= False	
		self.FNALBox.lock.release()
		self.logger.info("WORKER: lock on FNALBox released")
		
	## Function to start a test
	# implemented as a is a Pyqt slot
	@pyqtSlot(str)
	def SendModuleTestCmd(self,cmd):
		self.logger.info("WORKER: Executing "+cmd)
		subprocess.run(cmd.split(" "))
		
		
	###########################################################################
	## Safe operation functions. Directly called from "Manual Operation tab"
	###########################################################################
	
	## Function to select the SetPoint of the Julabo
	# implemented as a is a Pyqt slot
	# NOT Executed if:
	# - JULABO and FNAL info are not updated	
	# - JULABO is ON and the selected setpoint has a target temperature below the DewPoint
	# - TCP socket is not connected and connection attempt fails	
	# Control on cmd execution: read back from instrument
	@pyqtSlot(int)	
	def Ctrl_SelSp_Cmd(self,Sp_id, PopUp=True):
		self.last_op_ok= True
		self.logger.info("WORKER: Selecting JULABO Sp"+str(Sp_id+1))
		if not (self.SharedDict["Julabo_updated"] and self.SharedDict["FNALBox_updated"]):
			Warning_str = "Operation can't be performed"
			Reason_str = "Julabo and/or FNAL box info are not updated"
			if PopUp:
				self.Request_msg.emit(Warning_str,Reason_str)
			self.last_op_ok= False
			return
			
		if (self.SharedDict["Ctrl_StatusJulabo"].text().find("START") != -1):
			targetT = -100.0
			if Sp_id == 0 :
				targetT = float(self.SharedDict["Ctrl_Sp1"].text())
			elif Sp_id == 1 :
				targetT = float(self.SharedDict["Ctrl_Sp2"].text())
			elif Sp_id == 2 :
				targetT = float(self.SharedDict["Ctrl_Sp3"].text())

			if targetT  < float(self.SharedDict["Ctrl_IntDewPoint"].text()):
				Warning_str = "Operation can't be performed"
				Reason_str = "Set point is configured with a temperature below internal dew point"
				if PopUp:
					self.Request_msg.emit(Warning_str,Reason_str)
				self.last_op_ok= False
				return
		self.Julabo.lock.acquire()
		self.logger.debug("WORKER: Sending Julabo cmd" )
		if not self.Julabo.is_connected :
			self.Julabo.connect()
		if self.Julabo.is_connected :
			try:
				self.Julabo.sendTCP("out_mode_01 "+str(Sp_id))
				self.logger.info("WORKER: JULABO cmd sent")
				self.Julabo.sendTCP("in_mode_01")
				reply = self.Julabo.receive()
				if (reply != "None" and reply != "TCP error"):
					Sp = str(int(reply.replace(" ", ""))+1)
					self.SharedDict["Ctrl_TSp"].setText(Sp)
				if self.SharedDict["Ctrl_TSp"].text()[:1]=="1":
					self.SharedDict["Ctrl_TargetTemp"].setText(self.SharedDict["Ctrl_Sp1"].text())
				elif self.SharedDict["Ctrl_TSp"].text()[:1]=="2":
					self.SharedDict["Ctrl_TargetTemp"].setText(self.SharedDict["Ctrl_Sp2"].text())
				elif self.SharedDict["Ctrl_TSp"].text()[:1]=="3":
					self.SharedDict["Ctrl_TargetTemp"].setText(self.SharedDict["Ctrl_Sp3"].text())
			except Exception as e:
				self.logger.error(e)
				self.last_op_ok= False
		else:
				Warning_str = "Operation can't be performed"
				Reason_str = "Can't connect to JULABO"
				if PopUp:
					self.Request_msg.emit(Warning_str,Reason_str)
				self.last_op_ok= False
		
		self.Julabo.lock.release()
			
	## Function to select the target temperature of a JULABO SetPoint
	# implemented as a is a Pyqt slot
	# NOT Executed if:
	# - JULABO and FNAL info are not updated	
	# - JULABO is ON and the selected setpoint has a target temperature below the DewPoint
	# - TCP socket is not connected and connection attempt fails	
	# Control on cmd execution: read back from instrument	
	@pyqtSlot(int,float)	
	def Ctrl_SetSp_Cmd(self,Sp_id,value, PopUp=True):
		self.last_op_ok= True
		self.logger.info("WORKER: Setting JULABO Sp"+str(Sp_id+1)+ " to " +str(value))
		if not (self.SharedDict["Julabo_updated"] and self.SharedDict["FNALBox_updated"]):
			Warning_str = "Operation can't be performed"
			Reason_str = "Julabo and/or FNAL box info are not updated"
			if PopUp:
				self.Request_msg.emit(Warning_str,Reason_str)
			self.last_op_ok= False
			return	
		if (self.SharedDict["Ctrl_StatusJulabo"].text().find("START") != -1):
			Sp_actual = int(self.SharedDict["Ctrl_TSp"].text())-1
			if Sp_actual==Sp_id and  value  < float(self.SharedDict["Ctrl_IntDewPoint"].text()):
				Warning_str = "Operation can't be performed"
				Reason_str = "Attempting to set target temperature of the active set point below internal dew point"
				self.logger.warning(Warning_str)
				self.logger.warning(Reason_str)
				if PopUp:
					self.Request_msg.emit(Warning_str,Reason_str)
				self.last_op_ok= False
				return
		self.Julabo.lock.acquire()
		self.logger.debug("WORKER: Sending Julabo cmd" )
		if not self.Julabo.is_connected :
			self.Julabo.connect()
		if self.Julabo.is_connected :
			try:
				self.Julabo.sendTCP("out_sp_0"+str(Sp_id)+" "+str(value))
				self.logger.info("WORKER: JULABO cmd sent")					
				self.Julabo.sendTCP("in_sp_0"+str(Sp_id))
				reply = self.Julabo.receive()
				if (reply != "None" and reply != "TCP error"):
					self.SharedDict["Ctrl_Sp"+str(Sp_id+1)].setText(reply.replace(" ", ""))
				if self.SharedDict["Ctrl_TSp"].text()[:1]=="1":
					self.SharedDict["Ctrl_TargetTemp"].setText(self.SharedDict["Ctrl_Sp1"].text())
				elif self.SharedDict["Ctrl_TSp"].text()[:1]=="2":
					self.SharedDict["Ctrl_TargetTemp"].setText(self.SharedDict["Ctrl_Sp2"].text())
				elif self.SharedDict["Ctrl_TSp"].text()[:1]=="3":
					self.SharedDict["Ctrl_TargetTemp"].setText(self.SharedDict["Ctrl_Sp3"].text())
			except Exception as e:
				self.logger.error(e)
				self.last_op_ok= False	
		else:
			
				Warning_str = "Operation can't be performed"
				Reason_str = "Can't connect to JULABO"
				if PopUp:
					self.Request_msg.emit(Warning_str,Reason_str)
				self.last_op_ok= False
		self.Julabo.lock.release()

	## Function to select the target temperature of a JULABO SetPoint
	# implemented as a is a Pyqt slot
	# NOT Executed if:
	# - POWERING ON with JULABO and FNAL info are not updated	
	# - POWERING ON with target temp below DewPoint	
	# - POWERING ON with door not locked	
	# - POWERING ON with door not closed	
	# - TCP socket is not connected and connection attempt fails
	# Control on cmd execution: read back from instrument			
	@pyqtSlot(bool)	
	def Ctrl_PowerJulabo_Cmd(self,switch, PopUp=True):
		self.last_op_ok= True
		
		if not switch:  # power off
			self.logger.info("WORKER: Powering Julabo OFF")
			self.Julabo.lock.acquire()
			self.logger.debug("WORKER: Sending Julabo cmd" )
			if not self.Julabo.is_connected :
				self.Julabo.connect()
			if self.Julabo.is_connected :
				try:
					self.Julabo.sendTCP("out_mode_05 0")
					self.logger.info("WORKER: JULABO cmd sent")
					self.Julabo.sendTCP("status")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.SharedDict["Ctrl_StatusJulabo"].setText(reply)
					if self.SharedDict["Ctrl_StatusJulabo"].text().find("START")!=-1:
						self.SharedDict["Ctrl_StatusJulabo"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
					else:
						self.SharedDict["Ctrl_StatusJulabo"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ");
				except Exception as e:
					self.logger.error(e)
					self.last_op_ok= False	
						
			self.Julabo.lock.release()
		else:	
			self.logger.info("WORKER: Powering Julabo ON")
			if not (self.SharedDict["Julabo_updated"] and self.SharedDict["FNALBox_updated"]):
				Warning_str = "Operation can't be performed"
				Reason_str = "Julabo and/or FNAL box info are not updated"
				if PopUp:
					self.Request_msg.emit(Warning_str,Reason_str)
				self.last_op_ok= False
				return
			if float(self.SharedDict["Ctrl_TargetTemp"].text())< float(self.SharedDict["Ctrl_IntDewPoint"].text()):
				Warning_str = "Operation can't be performed"
				Reason_str = "Attempting to start unit with target temperature below internal dew point"
				if PopUp:
					self.Request_msg.emit(Warning_str,Reason_str)
				self.last_op_ok= False
				return
			if self.SharedDict["Ctrl_StatusLock"].text() != "LOCKED":
				Warning_str = "Operation can't be performed"
				Reason_str = "Attempting to start unit with door magnet not locked"
				if PopUp:
					self.Request_msg.emit(Warning_str,Reason_str)
				self.last_op_ok= False
				return
			if not (self.SharedDict["Ctrl_StatusDoor"].text() == "CLOSED"):
				Warning_str = "Operation can't be performed"
				Reason_str = "BurnIn door is NOT CLOSED"
				if PopUp:
					self.Request_msg.emit(Warning_str,Reason_str)
				self.last_op_ok= False
				return
				
			self.Julabo.lock.acquire()
			self.logger.debug("WORKER: Sending Julabo cmd" )
			if not self.Julabo.is_connected :
				self.Julabo.connect()
			if self.Julabo.is_connected :
				try:
					self.Julabo.sendTCP("out_mode_05 1")
					self.logger.info("WORKER: JULABO cmd sent")
					self.Julabo.sendTCP("status")
					reply = self.Julabo.receive()
					if (reply != "None" and reply != "TCP error"):
						self.SharedDict["Ctrl_StatusJulabo"].setText(reply)
					if self.SharedDict["Ctrl_StatusJulabo"].text().find("START")!=-1:
						self.SharedDict["Ctrl_StatusJulabo"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
					else:
						self.SharedDict["Ctrl_StatusJulabo"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ");
				except Exception as e:
					self.logger.error(e)
					self.last_op_ok= False	
			
			else:
			
				Warning_str = "Operation can't be performed"
				Reason_str = "Can't connect to JULABO"
				if PopUp:
					self.Request_msg.emit(Warning_str,Reason_str)
				self.last_op_ok= False
			self.Julabo.lock.release()
                    
					

					
	## Function to lock/unlock the door (magnet)
	# implemented as a is a Pyqt slot
	# NOT Executed if:
	# - UNLOCK with JULABO/FNAL/M5 info not updated	
	# - UNLOCK with minimal internal temp below EXTERNAL DewPoint
	# - UNLOCK with JULABO ON and taget temp below external dewpoint
	# - TCP socket is not connected and connection attempt fails	
	# Control on cmd execution: reply check from FNAL Box	
	@pyqtSlot(bool)	
	def Ctrl_SetLock_Cmd(self,switch, PopUp=True):
		self.last_op_ok= True
		
		lock = "LOCKED" if switch else "UNLOCK"
		cmd = "[5011]" if switch else "[5010]"

		self.logger.info("WORKER: Setting door magnet to: "+lock)
		if (not switch):
			
			if not (self.SharedDict["Julabo_updated"] and self.SharedDict["FNALBox_updated"] and self.SharedDict["M5_updated"]):
				Warning_str = "Operation can't be performed"
				Reason_str = "Julabo, FNAL box or M5 infos are not updated"
				if PopUp:
					self.Request_msg.emit(Warning_str,Reason_str)
				self.last_op_ok= False
				return
			if (self.SharedDict["Ctrl_StatusJulabo"].text().find("START")!=-1) and (float(self.SharedDict["Ctrl_TargetTemp"].text()) < float(self.SharedDict["Ctrl_ExtDewPoint"].text())):
				Warning_str = "Operation can't be performed"
				Reason_str = "JULABO is ON with target temp below external dew point"
				if PopUp:
					self.Request_msg.emit(Warning_str,Reason_str)
				self.last_op_ok= False
				return
			if self.SharedDict["Ctrl_LowerTemp"] < float(self.SharedDict["Ctrl_ExtDewPoint"].text()):
				Warning_str = "Operation can't be performed"
				Reason_str = "Internal minimum temperature below external dew point. Retry later"
				if PopUp:
					self.Request_msg.emit(Warning_str,Reason_str)
				self.last_op_ok= False
				return
				
		self.FNALBox.lock.acquire()
		self.logger.debug("WORKER: Sending FNAL Box cmd" )
		if not self.FNALBox.is_connected :
			self.FNALBox.connect()
		if self.FNALBox.is_connected :
			try:
				self.FNALBox.sendTCP(cmd)
				self.logger.info("WORKER: FNAL Box cmd sent: " + cmd)
				time.sleep(FNAL_SLEEP_AFTER_TCP)
				reply = self.FNALBox.receive()
				if reply[-3:]=="[*]":
					self.SharedDict["Ctrl_StatusLock"].setText(lock)
					self.logger.info("WORKER: Done")
				else:
					self.SharedDict["Ctrl_StatusLock"].setText("?")
					self.logger.error("WORKER: uncorrect reply from FNAL Box: "+reply)
					self.last_op_ok= False

			except Exception as e:
				self.logger.error(e)
				self.SharedDict["Ctrl_StatusLock"].setText("?")	
				self.last_op_ok= False
		
		else:
			Warning_str = "Operation can't be performed"
			Reason_str = "Can't connect to FNAL box"
			if PopUp:
				self.Request_msg.emit(Warning_str,Reason_str)
			self.last_op_ok= False			
		self.FNALBox.lock.release()
		
	## Function to select LOW/HIGH dry air flow
	# implemented as a is a Pyqt slot
	# NOT Executed if:
	# - TCP socket is not connected and connection attempt fails	
	# Control on cmd execution: reply check from FNAL Box		
	@pyqtSlot(bool)	
	def Ctrl_SetHighFlow_Cmd(self,switch, PopUp=True):
		self.last_op_ok= True
		
		flow = "HIGH" if switch else "LOW"
		cmd = "[5021]" if switch else "[5020]"

		self.logger.info("WORKER: Switching dry air flow to "+flow)
		self.FNALBox.lock.acquire()
		self.logger.debug("WORKER: Sending FNAL Box cmd" )
		if not self.FNALBox.is_connected :
			self.FNALBox.connect()
		if self.FNALBox.is_connected :
			try:
				self.FNALBox.sendTCP(cmd)
				self.logger.info("WORKER: FNAL Box cmd sent: " + cmd)
				time.sleep(FNAL_SLEEP_AFTER_TCP)
				reply = self.FNALBox.receive()
				if reply[-3:]=="[*]":
					self.SharedDict["Ctrl_StatusFlow"].setText(flow)
					self.logger.info("WORKER: Done")
				else:
					self.SharedDict["Ctrl_StatusFlow"].setText("?")
					self.logger.error("WORKER: uncorrect reply from FNAL Box: "+reply)
					self.last_op_ok= False

			except Exception as e:
				self.logger.error(e)
				self.SharedDict["Ctrl_StatusFlow"].setText("?")
				self.last_op_ok= False

		else:	
			Warning_str = "Operation can't be performed"
			Reason_str = "Can't connect to FNAL box"
			if PopUp:
				self.Request_msg.emit(Warning_str,Reason_str)
			self.last_op_ok= False				
					
		self.FNALBox.lock.release()
		
	## Function to power ON/OFF individual LV channels
	# implemented as a is a Pyqt slot
	# NOT Executed if:
	# - CAEN INFO are not updated
	# - POWER ON with JULABO OFF
	# - one of the slots selected by the user does not have a definet LV channel
	# - trying to switch off a slot with HV ON
	# Control on cmd execution: none
	@pyqtSlot(bool)	
	def Ctrl_PowerLV_Cmd(self,switch,Channel_list=[], PopUp=True):
		self.last_op_ok= True
		if PopUp:
			Channel_list.clear()
		power = "On" if switch else "Off"
		if not (self.SharedDict["CAEN_updated"]):
			Warning_str = "Operation can't be performed"
			Reason_str = "CAEN infos are not updated"
			if PopUp:
				self.Request_msg.emit(Warning_str,Reason_str)
			self.last_op_ok= False
			return
		if switch and self.SharedDict["Ctrl_StatusJulabo"].text().find("START")==-1:
			Warning_str = "Operation can't be performed"
			Reason_str = "JULABO is not ON"
			if PopUp:
				self.Request_msg.emit(Warning_str,Reason_str)
			self.last_op_ok= False
			return	
		if len(Channel_list)==0:
			for row in range(NUM_BI_SLOTS):
				if self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_NAME_COL).isSelected():
					ch_name = self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_NAME_COL).text()
					if (ch_name == "?"):
						Warning_str = "Operation can't be performed"
						Reason_str = "Can't turn OFF LV for slot "+str(row+1)+ " beacause LV ch. name is UNKNOWN"
						if PopUp:
							self.Request_msg.emit(Warning_str,Reason_str)
						self.last_op_ok= False
						return
					HV_defined = True if self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_NAME_COL).text() != "?" else False	
					if (not switch) and  HV_defined and (self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_STAT_COL).text() != "OFF"):  # attempt to power down LV with HV not off
						Warning_str = "Operation can't be performed"
						Reason_str = "Can't turn OFF LV for slot "+str(row+1)+ " beacause HV is ON or UNKNOWN"
						if PopUp:
							self.Request_msg.emit(Warning_str,Reason_str)
						self.last_op_ok= False
						return
					Channel_list.append(ch_name)
				
		self.logger.info("WORKER: Setting LV "+power+ " for ch " +str(Channel_list))
		for channel in Channel_list:
			self.SendCAENControllerCmd("Turn"+power+",PowerSupplyId:caen,ChannelId:"+channel)	
			
	## Function to power ON/OFF individual HV channels
	# implemented as a is a Pyqt slot
	# NOT Executed if:
	# - CAEN INFO are not updated
	# - POWER ON with door not CLOSED
	# - one of the slots selected by the user does not have a defined HV channel
	# - trying to switch on a slot with LV OFF
	# Control on cmd execution: none
	@pyqtSlot(bool)	
	def Ctrl_PowerHV_Cmd(self,switch,Channel_list=[],PopUp=True):
		self.last_op_ok= True
		if PopUp:
			Channel_list.clear()
		power = "On" if switch else "Off"
		if not (self.SharedDict["CAEN_updated"] and self.SharedDict["FNALBox_updated"]):
			Warning_str = "Operation can't be performed"
			Reason_str = "CAEN and/or FNAL infos are not updated"
			if PopUp:
				self.Request_msg.emit(Warning_str,Reason_str)
			self.last_op_ok= False
			return
		if switch and (not (self.SharedDict["Ctrl_StatusDoor"].text() == "CLOSED")):
			Warning_str = "Operation can't be performed"
			Reason_str = "BurnIn door is NOT CLOSED"
			if PopUp:
				self.Request_msg.emit(Warning_str,Reason_str)
			self.last_op_ok= False
			return
		
		if len(Channel_list)==0:
			for row in range(NUM_BI_SLOTS):
				if self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_NAME_COL).isSelected():
					ch_name = self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_NAME_COL).text() 
					if (ch_name == "?"):
						Warning_str = "Operation can't be performed"
						Reason_str = "Can't turn OFF HV for slot "+str(row+1)+ " beacause HV ch. name is UNKNOWN"
						if PopUp:
							self.Request_msg.emit(Warning_str,Reason_str)
						self.last_op_ok= False
						return
					if (switch) and (self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_STAT_COL).text() != "ON"):  # attempt to power up HV with LV not on
						Warning_str = "Operation can't be performed"
						Reason_str = "Can't turn OFF HV for slot "+str(row+1)+ " beacause LV is OFF or UNKNOWN"
						if PopUp:
							self.Request_msg.emit(Warning_str,Reason_str)
						self.last_op_ok= False
						return
					Channel_list.append(ch_name)
				
		self.logger.info("WORKER: Setting HV "+power+ " for ch " +str(Channel_list))
		for channel in Channel_list:
			self.SendCAENControllerCmd("Turn"+power+",PowerSupplyId:caen,ChannelId:"+channel)
	
	## Function to set indicidual LV/HV channels
	# implemented as a is a Pyqt slot
	# NOT Executed if:
	# - CAEN INFO are not updated
	# - POWER ON with door not CLOSED
	# - one of the slots selected by the user does not have a defined LV/HV setpoint
	# Control on cmd execution: none
	@pyqtSlot(str)	
	def Ctrl_VSet_Cmd(self,VType,Channel_list=[],NewValue_list=[], PopUp=True):
		self.last_op_ok= True
		if PopUp:
			Channel_list.clear()
			NewValue_list.clear()
	
		if VType != "LV" and VType != "HV":
			self.logger.error("WORKER: Received unknow Voltage type string ")
			return
			
		ColOffset = CTRLTABLE_LV_NAME_COL if VType=="LV" else CTRLTABLE_HV_NAME_COL;
		if not (self.SharedDict["CAEN_updated"]):
			Warning_str = "Operation can't be performed"
			Reason_str = "CAEN infos are not updated"
			if PopUp:
				self.Request_msg.emit(Warning_str,Reason_str)
			self.last_op_ok= False
			return
		if len(Channel_list) != len(NewValue_list):
			Warning_str = "Operation can't be performed"
			Reason_str = "Provided ch list and value list doesn not match in length"
			if PopUp:
				self.Request_msg.emit(Warning_str,Reason_str)
			self.last_op_ok= False
			return
			
		if len(Channel_list)==0:
			for row in range(NUM_BI_SLOTS):
				if self.SharedDict["CAEN_table"].item(row,ColOffset).isSelected():
					ch_name = self.SharedDict["CAEN_table"].item(row,ColOffset).text() 
					if (ch_name == "?"):
						Warning_str = "Operation can't be performed"
						Reason_str = "Can't set LV for  slot "+str(row+1)+ " beacause LV ch. name is UNKNOWN"
						if PopUp:
							self.Request_msg.emit(Warning_str,Reason_str)
						self.last_op_ok= False
						return
					if (self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_VSET_COL+ColOffset).text() == "?"): 
						Warning_str = "Operation can't be performed"
						Reason_str = "Can't set LV/HV for  slot "+str(row+1)+ " beacause current setpoint is UNKNOWN"
						if PopUp:
							self.Request_msg.emit(Warning_str,Reason_str)
						self.last_op_ok= False
						return
					self.SharedDict["WaitInput"]=True
					Request_str="New " +VType+ " Slot "+str(row+1)
					ValueNow = 0.0
					try :
						ValueNow = float(self.SharedDict["CAEN_table"].item(row,2+ColOffset).text())
					except Exception as e:
						self.logger.error(e)
						
					if VType == "LV":
						self.Request_input_dsb.emit(Request_str,ValueNow,MIN_LV,MAX_HV)
					else:
						self.Request_input_dsb.emit(Request_str,ValueNow,MIN_HV,MAX_HV)
						
					while self.SharedDict["WaitInput"]:
						time.sleep(0.1)
					if self.SharedDict["Input"]!=-1:
						NewValue_list.append(self.SharedDict["Input"])
						Channel_list.append(ch_name)
		
		self.logger.info("WORKER: Setting LV for ch " +str(Channel_list))
		self.logger.info("WORKER: New values: " +str(NewValue_list))
		for idx,channel in enumerate(Channel_list):
			self.SendCAENControllerCmd("SetVoltage,PowerSupplyId:caen,ChannelId:"+channel+",Voltage:"+str(NewValue_list[idx]))





	###########################################################################
	## BI main function and related
	###########################################################################
	
	
	
	## BI main function
	# implemented as a is a Pyqt slot
	@pyqtSlot()			
	def BI_Start_Cmd(self):
	
		self.SharedDict["BI_Active"]=True
		self.logger.info("Starting BurnIN...")
		
		#creating parameter dictionary for the current session
		session_dict={}
		session_dict["Action"]				= "Setup"
		session_dict["Cycle"]				= 1
		session_dict["LowTemp"]				= self.SharedDict["BI_LowTemp"]
		session_dict["UnderRamp"]			= self.SharedDict["BI_UnderRamp"]
		session_dict["UnderKeep"]			= self.SharedDict["BI_UnderKeep"]
		session_dict["HighTemp"]			= self.SharedDict["BI_HighTemp"]
		session_dict["NCycles"]				= self.SharedDict["BI_NCycles"]
		session_dict["Operator"]			= self.SharedDict["BI_Operator"]
		session_dict["Description"]			= self.SharedDict["BI_Description"]
		session_dict["Session"]				= "-1"
		session_dict["ActiveSlots"]			= self.SharedDict["BI_ActiveSlots"]
		session_dict["ModuleIDs"]			= self.SharedDict["BI_ModuleIDs"]
		session_dict["Dry"]					= self.SharedDict["BI_Dry"]
		session_dict["Timestamp"]			= datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
		
		
		
		#check if file session already exists (aka a session was stopped or crashed)
		if (os.path.exists("Session.json")):
			self.logger.info("Found session file.")
			self.SharedDict["WaitInput"]=True
			self.Request_confirm_sig.emit("Resume last session?")
			while self.SharedDict["WaitInput"]:
						time.sleep(0.1)
			if self.SharedDict["Confirmed"]:
				try:
					with open('Session.json') as json_file:
						session_dict={}
						session_dict = json.load(json_file)
						self.logger.info(session_dict)
						#updating values in main GUI tab
						self.BI_Update_GUI_sig.emit(session_dict)
						self.logger.info("BI :Previous session parameters loaded")
						self.logger.info("Current Session: "+session_dict["Session"])
						self.logger.info("Current Cycle: "+str(session_dict["Cycle"]))
						self.logger.info("Recovery status: "+session_dict["Action"])
						
				except Exception as e:
					self.logger.error(e)
					self.logger.error("BI :Error reloading session parameters from Json file")
					self.BI_Abort("Error while recovering session info. Please start new session")
					return
			else:
				self.logger.info("Prevoius session overrided. Starting new session")
				self.BI_Update_Status_file(session_dict)
				self.DB_interface.StartSesh(session_dict)
				self.BI_Clear_Monitor_sig.emit()

		else:
			self.logger.info("No session file found. Starting new BurnIn session")
			self.BI_Update_Status_file(session_dict)
			self.DB_interface.StartSesh(session_dict)
			self.BI_Clear_Monitor_sig.emit()

		self.SharedDict["TestSession"]=session_dict["Session"]
		
		
		# starting setup/recovery procedure
		
		if (session_dict["Action"]=="Setup"):
			self.SharedDict["BI_Status"].setText("Setup")
		else:
			self.SharedDict["BI_Status"].setText("Recovery")
			
		self.SharedDict["BI_Action"].setText("Setup")
		self.SharedDict["BI_Cycle"].setText(str(session_dict["Cycle"])+" of "+str(session_dict["NCycles"]))
					
		
		#checking sub-system information
			
		if not (self.SharedDict["CAEN_updated"] and self.SharedDict["FNALBox_updated"] and self.SharedDict["Julabo_updated"]):
			self.BI_Abort("CAEN/FNAL/JULABO infos are not updated")
			return
		if not (self.SharedDict["Ctrl_StatusDoor"].text() == "CLOSED"):
			self.BI_Abort("DOOR is not closed!")
			return
		self.logger.info("BurnIn test started...")
		
		#selecting slots under test : LV/HV names defined && slot marked as active in BI tab
		
		LV_Channel_list=[]
		HV_Channel_list=[]
		Slot_list=[]
		
		for row in range(NUM_BI_SLOTS):
			LV_ch_name = self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_NAME_COL).text()
			HV_ch_name = self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_NAME_COL).text() 
			if (LV_ch_name != "?" and HV_ch_name != "?" and session_dict["ActiveSlots"][row]):
				LV_Channel_list.append(LV_ch_name)
				HV_Channel_list.append(HV_ch_name)
				Slot_list.append(row)

		
		self.logger.info("BurnIn test active slots: "+str(Slot_list))
		self.logger.info("BurnIn test HV names: "+str(HV_Channel_list))
		self.logger.info("BurnIn test LV names: "+str(LV_Channel_list))			   
		
		PopUp=False
		
		#lock magnet
		if not self.BI_Action(self.Ctrl_SetLock_Cmd,True,True,PopUp):
			return
			
		#start high flow if needed
		try:
			dp = float(self.SharedDict["Ctrl_IntDewPoint"].text())
		except Exception as e:
			dp=0.0
		if dp < BI_HIGHFLOW_THRESHOLD and self.SharedDict["Ctrl_StatusFlow"].text()=="LOW":
			if not self.BI_Action(self.Ctrl_SetHighFlow_Cmd,True, True,PopUp):
				return
			
		#sel SP	
		if not self.BI_Action(self.Ctrl_SelSp_Cmd,True,0,PopUp):
			return
				
		#start JULABO	
		if not self.BI_Action(self.Ctrl_PowerJulabo_Cmd,True,True,PopUp):
			return
		
		##start LV
		self.SharedDict["BI_Action"].setText("Start LVs")
		if not self.BI_Action(self.Ctrl_PowerLV_Cmd,True,True,LV_Channel_list,PopUp):
			return
		time.sleep(BI_SLEEP_AFTER_VSET)
		
		#check all LVs are ON
		for row in Slot_list:
			if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_STAT_COL).text()!="ON"):
				self.BI_Abort("BI aborted: some LVs was not turned ON")
				return
		
		#start HV
		self.SharedDict["BI_Action"].setText("Start HVs")
		if not self.BI_Action(self.Ctrl_PowerHV_Cmd,True,True,HV_Channel_list,PopUp):
			return
		
		time.sleep(BI_SLEEP_AFTER_VSET)
		#check all HVs are ON
		for row in Slot_list:
			if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_STAT_COL).text()!="ON"):
				self.BI_Abort("BI aborted: some HVs was not turned ON")
				return
			
		
		self.SharedDict["BI_Status"].setText("Cycling")

		cycle=session_dict["Cycle"]-1
		NCycles	= session_dict["NCycles"]
		######cycle start
		if (session_dict["Action"]=="Setup"):
			session_dict["Action"]="RampDown"
		else:
			self.logger.info("BI: recovered from cycle "+str(cycle+1) + " of "+str(NCycles))
		
		while(cycle < NCycles):
			if (session_dict["Action"]=="RampDown"):
				session_dict["Cycle"]=cycle+1
				self.BI_Update_Status_file(session_dict)
				self.logger.info("BI: starting cycle "+str(cycle+1) + " of "+str(NCycles))
				
				self.SharedDict["BI_Cycle"].setText(str(cycle+1)+"/"+str(NCycles))
				self.logger.info("BI: runmping down...")
				self.SharedDict["BI_Action"].setText("Cooling")
				if float(self.SharedDict["LastFNALBoxTemp0"].text()) > session_dict["LowTemp"]:  #expected
					if not self.BI_Action(self.BI_GoLowTemp,True,session_dict,session_dict["LowTemp"]):
						self.logger.info("BI: cooling")
						return
				else:
					if not self.BI_Action(self.BI_GoHighTemp,True,session_dict,session_dict["LowTemp"]):
						return
				session_dict["Action"]="ColdTest"
				
			if (session_dict["Action"]=="ColdTest"):
				self.BI_Update_Status_file(session_dict)
				self.logger.info("BI: testing...")
				self.SharedDict["BI_Action"].setText("Cold Module test")
				self.SharedDict["BI_TestActive"]=True
				if not self.BI_Action(self.BI_StartTest_Cmd,False,session_dict):
						return
				self.SharedDict["BI_TestActive"]=False
				session_dict["Action"]="RampUp"
				
			if (session_dict["Action"]=="RampUp"):
				self.BI_Update_Status_file(session_dict)
				self.logger.info("BI: going to high temp")
				self.SharedDict["BI_Action"].setText("Heating")
				if float(self.SharedDict["LastFNALBoxTemp0"].text()) < session_dict["HighTemp"]:  #expected
					self.logger.info("BI: heating")
					if not self.BI_Action(self.BI_GoHighTemp,True,session_dict,session_dict["HighTemp"]):
						return
				else:
					if not self.BI_Action(self.BI_GoLowTemp,True,session_dict,session_dict["HighTemp"]):
						return
				session_dict["Action"]="HotTest"
				
			if (session_dict["Action"]=="HotTest"):
				self.BI_Update_Status_file(session_dict)
				self.logger.info("BI: testing...")
				self.SharedDict["BI_Action"].setText("Hot Module test")
				self.SharedDict["BI_TestActive"]=True
				if not self.BI_Action(self.BI_StartTest_Cmd,False,session_dict):
						return
				self.SharedDict["BI_TestActive"]=False
			
				self.logger.info("BI: ended cycle "+str(cycle+1) + " of "+str(NCycles))
				#self.SharedDict["BI_ProgressBar"].setValue((cycle+1)/NCycles*100)
				session_dict["Action"]="RampDown"
				cycle=cycle+1
		
		if (os.path.exists("Session.json")):		
			os.remove("Session.json")
			self.logger.info("BI: Session json file deleted")
		else:
			self.logger.info("BI: Could not locate session json file")
		
		self.SharedDict["BI_Status"].setText("Stopping")
		
		#stop HV
		self.SharedDict["BI_Action"].setText("Stop HVs")
		if not self.BI_Action(self.Ctrl_PowerHV_Cmd,True,False,HV_Channel_list,PopUp):
			return
		time.sleep(BI_SLEEP_AFTER_VSET)
		#check HV stop
		for row in Slot_list:
			if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_STAT_COL).text()!="OFF"):
				self.BI_Abort("BI aborted: some LVs was not turned OFF")
				return
			
		
		#stop LV
		self.SharedDict["BI_Action"].setText("Stop LVs")
		if not self.BI_Action(self.Ctrl_PowerLV_Cmd,True,False,LV_Channel_list,PopUp):
			return
		time.sleep(BI_SLEEP_AFTER_VSET)
		#check LV stop	
		for row in Slot_list:
			if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_STAT_COL).text()!="OFF"):
				self.BI_Abort("BI aborted: some HVs was not turned OFF")
				return
				
		#put JULABO to 20 degree	
		self.SharedDict["BI_Action"].setText("Closing")
		if not self.BI_Action(self.Ctrl_SetSp_Cmd,True,0,20.0,PopUp):
			return	
		
		#lower dry air flow
		if self.SharedDict["Ctrl_StatusFlow"].text()=="HIGH":
			if not self.BI_Action(self.Ctrl_SetHighFlow_Cmd,True, False,PopUp):
				return
				
		self.logger.info("BurnIn test COMPLETED SUCCESFULLY!")
		self.SharedDict["BI_Active"]=False
		self.SharedDict["BI_Status"].setText("Idle")
		self.SharedDict["BI_Action"].setText("None")
		self.SharedDict["BI_StopRequest"]=False
		if os.path.exists("Session.json"):
			os.remove("Session.json")
		self.BI_terminated.emit()
	
	## BI Abort function	
	def BI_Abort(self,Reason_str):
	
			Warning_str = "BURN IN test failed"
			self.SharedDict["BI_Status"].setText("Aborted")
			#self.Request_msg.emit(Warning_str,Reason_str)
			self.SharedDict["BI_Active"]=False
			self.SharedDict["BI_StopRequest"]=False
			self.sharedDict["BI_TestActive"]=False
			self.BI_terminated.emit()
		
	
	## BI Action function. used to execute a defined operation.		
	def BI_Action(self,Action,abort_if_fail, *args):
		retry=BI_ACTION_RETRIES
		while retry:
			Action(*args)
			if self.SharedDict["BI_StopRequest"]:
				self.BI_Abort("BI: aborted for user or Supervisor request")
				return False
			if not (self.last_op_ok):
				self.logger.warning("BI: failed to do action...new try in 10 sec")
				time.sleep(BI_ACTION_RETRY_SLEEP)
				retry=retry-1
			else:
				return True
		if abort_if_fail:
			self.BI_Abort("BI: failed to do action ("+str(BI_ACTION_RETRIES)+" times)...aborting")
			return False
		else:
			self.logger.warning("BI: failed to do action ("+str(BI_ACTION_RETRIES)+" times)...but going ahead with test")
			return True

	## BI function to ramp down in temp
	def BI_GoLowTemp(self,session_dict,LowTemp):
	
		TempTolerance		= BI_TEMP_TOLERANCE
		TempRampOffset		= session_dict["UnderRamp"]
		TempMantainOffset	= session_dict["UnderKeep"]
		
		last_step=False
		self.last_op_ok= True
		PopUp=False
		nextTemp = 0.0
		
		while (not last_step):
			try:
				dewPoint = float(self.SharedDict["Ctrl_IntDewPoint"].text())
			except Exception as e:
				self.logger.error(e)
				self.last_op_ok= False
				return
			
			if (LowTemp-TempRampOffset> dewPoint):
				nextTemp = LowTemp-TempRampOffset
				self.logger.info("BI: target low temp OK...")
				last_step = True
			else:
				nextTemp = dewPoint
				self.logger.info("BI: target low temp below dew point, going to dewPoint and rising flow...")
				if not self.BI_Action(self.Ctrl_SetHighFlow_Cmd,True, True,PopUp):
					return
				
			
			if not self.BI_Action(self.Ctrl_SetSp_Cmd,True,0,nextTemp,PopUp):
				self.last_op_ok= False
				return	
				
			while(True):
				try:
					dewPoint = float(self.SharedDict["Ctrl_IntDewPoint"].text())
					if dewpoint < BI_HIGHFLOW_THRESHOLD and self.SharedDict["Ctrl_StatusFlow"].text()=="HIGH":
						if not self.BI_Action(self.Ctrl_SetHighFlow_Cmd,True,False,PopUp):
							return
					elif self.SharedDict["Ctrl_StatusFlow"].text()=="LOW":
						if not self.BI_Action(self.Ctrl_SetHighFlow_Cmd,True,True,PopUp):
							return
					if (abs(float(self.SharedDict["LastFNALBoxTemp0"].text())-(nextTemp+TempRampOffset)) < TempTolerance):
						break
					if self.SharedDict["BI_StopRequest"]:
						self.last_op_ok= False
						return	
					if not (self.SharedDict["CAEN_updated"] and self.SharedDict["FNALBox_updated"] and self.SharedDict["Julabo_updated"]):
						self.last_op_ok= False
						return
					time.sleep(BI_SLEEP_AFTER_TEMP_CHECK)
				except Exception as e:
					pass
			
			
		# set target temperature mantain
		self.logger.info("BI: keep temperature ....")
		if not self.BI_Action(self.Ctrl_SetSp_Cmd,True,0,LowTemp-TempMantainOffset,PopUp):
			self.last_op_ok= False
			return
	
	## BI function to ramp up in temp
	def BI_GoHighTemp(self,session_dict,HighTemp):
	
		TempTolerance		= BI_TEMP_TOLERANCE
		TempRampOffset		= session_dict["UnderRamp"]
		TempMantainOffset	= session_dict["UnderKeep"]
		
		self.last_op_ok= True
		PopUp=False
		
		nextTemp=HighTemp+TempMantainOffset
		
		if not self.BI_Action(self.Ctrl_SetSp_Cmd,True,0,nextTemp,PopUp):
			self.last_op_ok= False
			return	
		
		self.logger.info("BI: heating....")	
		while(True):
			try:
				dewPoint = float(self.SharedDict["Ctrl_IntDewPoint"].text())
				if dewpoint < BI_HIGHFLOW_THRESHOLD and self.SharedDict["Ctrl_StatusFlow"].text()=="HIGH":
					if not self.BI_Action(self.Ctrl_SetHighFlow_Cmd,True,False,PopUp):
						return
				elif self.SharedDict["Ctrl_StatusFlow"].text()=="LOW":
					if not self.BI_Action(self.Ctrl_SetHighFlow_Cmd,True,True,PopUp):
						return
				if (abs(float(self.SharedDict["LastFNALBoxTemp0"].text())-HighTemp) < TempTolerance):
					break
				if self.SharedDict["BI_StopRequest"]:
					self.last_op_ok= False
					return	
				if not (self.SharedDict["CAEN_updated"] and self.SharedDict["FNALBox_updated"] and self.SharedDict["Julabo_updated"]):
					self.last_op_ok= False
					return
				time.sleep(BI_SLEEP_AFTER_TEMP_CHECK)
			except Exception as e:
				pass	
			
			
		# set target temperature mantain
		self.logger.info("BI: keep temperature ....")
		if not self.BI_Action(self.Ctrl_SetSp_Cmd,0,HighTemp-TempMantainOffset,PopUp):
			self.last_op_ok= False
			return

	def BI_Update_Status_file(self,session_dict):
	
		with open("Session.json", "w") as outfile: 
			json.dump(session_dict, outfile)

	def BI_StartTest_Cmd(self, session_dict):
			self.logger.info("Starting module test...")
			session=self.SharedDict["TestSession"]
			dry = session_dict["Dry"]
			self.last_op_ok= True
			if dry:
				self.logger.info("Dry run. Just waiting 20 s.")
				time.sleep(60)
				return True
			else:
				#create non-blocking process
				try:
					proc = subprocess.Popen(["python3", "moduleTest.py", session],
														cwd="/home/thermal/Ph2_ACF_docker/BurnIn_moduleTest",stdout=subprocess.PIPE, stderr=subprocess.PIPE)
					while(proc.returnCode==None):
						
						if self.SharedDict["BI_StopRequest"]:
							self.logger.error("WORKER: Aborting module test on external request")
							proc.kill()
							self.last_op_ok= False
							return
						try:
							outs, errs = proc.communicate(timeout=TEST_PROCESS_SLEEP)
						except TimeoutExpired:
							self.logger.info("WORKER: Waiting test completion....")
							self.logger.info("BI TEST SUBPROCESS: "+outs)
							self.logger.error("BI TEST SUBPROCESS: "+errs)
					
					if proc.returnCode ==0:
						self.logger.info("Module test succesfully completed with exit code "+proc.returnCode)
					else:
						self.logger.error("Module test failed with exit code "+proc.returnCode)
						self.last_op_ok= False
						
				except Exception as e:
					self.logger.error("WORKER: "+e)
					self.last_op_ok= False
							
	
	@pyqtSlot(bool)				
	def MT_StartTest_Cmd(self, dry=False, PupUp=False):
			self.logger.info("Starting module test...Please wait till completion")
			if PupUp:
				msg = QMessageBox()
				msg.setWindowTitle("Module test ongoing. Please wait...")
				msg.show()
			session=self.SharedDict["TestSession"]
			if dry:
				result = subprocess.run(["python3", "moduleTest.py", session, "--useExistingModuleTest","T2023_12_04_16_26_11_224929"],
													cwd="/home/thermal/Ph2_ACF_docker/BurnIn_moduleTest")
			else:
				result = subprocess.run(["python3", "moduleTest.py", session],
													cwd="/home/thermal/Ph2_ACF_docker/BurnIn_moduleTest")
			self.logger.info(result.stdout)
			self.logger.error(result.stderr)
			self.logger.info("Module test completed!")
			
	
	def MT_UploadDB_Cmd(self):
		pass
