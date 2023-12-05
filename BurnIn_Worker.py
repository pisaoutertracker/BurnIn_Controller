import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
import time
import datetime
import subprocess
from __Constant import *


class BurnIn_Worker(QObject):

	Request_msg = pyqtSignal(str,str)
	Request_input_dsb = pyqtSignal(str,float,float,float)
	BI_terminated = pyqtSignal()
	
	def __init__(self,configDict,logger, SharedDict, Julabo, FNALBox, CAENController):

	
		super(BurnIn_Worker,self).__init__();
		self.configDict=configDict
		self.logger = logger
		self.Julabo = Julabo
		self.FNALBox = FNALBox
		self.CAENController = CAENController
		self.SharedDict = SharedDict
		
		self.logger.info("Worker class initialized")
		self.last_op_ok= True
		
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
	
	@pyqtSlot(str)
	def SendFNALBoxCmd(self,cmd):
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
	
	@pyqtSlot(str)
	def SendModuleTestCmd(self,cmd):
		self.logger.info("WORKER: Executing "+cmd)
		subprocess.run(cmd.split(" "))
	
	@pyqtSlot(int)	
	def Ctrl_SelSp_Cmd(self,Sp_id, BI_Action=False):
		self.last_op_ok= True
		self.logger.info("WORKER: Selecting JULABO Sp"+str(Sp_id+1))
		if not (self.SharedDict["Julabo_updated"] and self.SharedDict["FNALBox_updated"]):
			Warning_str = "Operation can't be performed"
			Reason_str = "Julabo and/or FNAL box info are not updated"
			if not BI_Action:
				self.Request_msg.emit(Warning_str,Reason_str)
			self.last_op_ok= False
			return
		else:	
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
					if not BI_Action:
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
					if not BI_Action:
						self.Request_msg.emit(Warning_str,Reason_str)
					self.last_op_ok= False
			
			self.Julabo.lock.release()
			
	
	@pyqtSlot(int,float)	
	def Ctrl_SetSp_Cmd(self,Sp_id,value, BI_Action=False):
		self.last_op_ok= True
		self.logger.info("WORKER: Setting JULABO Sp"+str(Sp_id+1)+ " to " +str(value))
		if not (self.SharedDict["Julabo_updated"] and self.SharedDict["FNALBox_updated"]):
			Warning_str = "Operation can't be performed"
			Reason_str = "Julabo and/or FNAL box info are not updated"
			if not BI_Action:
				self.Request_msg.emit(Warning_str,Reason_str)
			self.last_op_ok= False
			return
		else:	
			if (self.SharedDict["Ctrl_StatusJulabo"].text().find("START") != -1):
				Sp_actual = int(self.SharedDict["Ctrl_TSp"].text())-1
				if Sp_actual==Sp_id and  value  < float(self.SharedDict["Ctrl_IntDewPoint"].text()):
					Warning_str = "Operation can't be performed"
					Reason_str = "Attempting to set target temperature of the active set point below internal dew point"
					self.logger.warning(Warning_str)
					self.logger.warning(Reason_str)
					if not BI_Action:
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
					if not BI_Action:
						self.Request_msg.emit(Warning_str,Reason_str)
					self.last_op_ok= False
			self.Julabo.lock.release()

		
	@pyqtSlot(bool)	
	def Ctrl_PowerJulabo_Cmd(self,switch, BI_Action=False):
		self.last_op_ok= True
		
		if not switch:
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
				if not BI_Action:
					self.Request_msg.emit(Warning_str,Reason_str)
				self.last_op_ok= False
				return
			else:	
				if float(self.SharedDict["Ctrl_TargetTemp"].text())< float(self.SharedDict["Ctrl_IntDewPoint"].text()):
					Warning_str = "Operation can't be performed"
					Reason_str = "Attempting to start unit with target temperature below internal dew point"
					if not BI_Action:
						self.Request_msg.emit(Warning_str,Reason_str)
					self.last_op_ok= False
					return
				if self.SharedDict["Ctrl_StatusLock"].text() != "LOCKED":
					Warning_str = "Operation can't be performed"
					Reason_str = "Attempting to start unit with door magnet not locked"
					if not BI_Action:
						self.Request_msg.emit(Warning_str,Reason_str)
					self.last_op_ok= False
					return
				else:
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
						if not BI_Action:
							self.Request_msg.emit(Warning_str,Reason_str)
						self.last_op_ok= False
					self.Julabo.lock.release()
                    
					

					
		
	@pyqtSlot(bool)	
	def Ctrl_SetLock_Cmd(self,switch, BI_Action=False):
		self.last_op_ok= True
		
		lock = "LOCKED" if switch else "UNLOCK"
		cmd = "[5011]" if switch else "[5010]"

		self.logger.info("WORKER: Setting door magnet to: "+lock)
		if (not switch):
			
			if not (self.SharedDict["Julabo_updated"] and self.SharedDict["FNALBox_updated"] and self.SharedDict["M5_updated"]):
				Warning_str = "Operation can't be performed"
				Reason_str = "Julabo, FNAL box or M5 infos are not updated"
				if not BI_Action:
					self.Request_msg.emit(Warning_str,Reason_str)
				self.last_op_ok= False
				return
			try:
				IntTemp_arr = [float(self.SharedDict["LastFNALBoxTemp1"].text()),float(self.SharedDict["LastFNALBoxTemp0"].text())]
				for i in range (NUM_BI_SLOTS):
					IntTemp_arr.append(float(self.SharedDict["LastFNALBoxOW"+str(i)].text())) 
				IntTemp_min = min(IntTemp_arr)
			except Exception as e:
				self.logger.error(e)
				self.last_op_ok= False
				return
			if (self.SharedDict["Ctrl_StatusJulabo"].text().find("START")!=-1) and (float(self.SharedDict["Ctrl_TargetTemp"].text()) < float(self.SharedDict["Ctrl_ExtDewPoint"].text())):
				Warning_str = "Operation can't be performed"
				Reason_str = "JULABO is ON with target temp below external dew point"
				if not BI_Action:
					self.Request_msg.emit(Warning_str,Reason_str)
				self.last_op_ok= False
				return
			if IntTemp_min < float(self.SharedDict["Ctrl_ExtDewPoint"].text()):
				Warning_str = "Operation can't be performed"
				Reason_str = "Internal minimum temperature below external dew point. Retry later"
				if not BI_Action:
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
			if not BI_Action:
				self.Request_msg.emit(Warning_str,Reason_str)
			self.last_op_ok= False			
		self.FNALBox.lock.release()
		
		
	@pyqtSlot(bool)	
	def Ctrl_SetHighFlow_Cmd(self,switch, BI_Action=False):
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
			if not BI_Action:
				self.Request_msg.emit(Warning_str,Reason_str)
			self.last_op_ok= False				
					
		self.FNALBox.lock.release()

	@pyqtSlot(bool)	
	def Ctrl_PowerLV_Cmd(self,switch,Channel_list=[], BI_Action=False):
		self.last_op_ok= True
		if not BI_Action:
			Channel_list.clear()
		power = "On" if switch else "Off"
		if not (self.SharedDict["CAEN_updated"]):
			Warning_str = "Operation can't be performed"
			Reason_str = "CAEN infos are not updated"
			if not BI_Action:
				self.Request_msg.emit(Warning_str,Reason_str)
			self.last_op_ok= False
			return
		if self.SharedDict["Ctrl_StatusJulabo"].text().find("START")==-1:
			Warning_str = "Operation can't be performed"
			Reason_str = "JULABO is not ON"
			if not BI_Action:
				self.Request_msg.emit(Warning_str,Reason_str)
			self.last_op_ok= False
			return	
		if len(Channel_list)==0:
			for row in range(NUM_BI_SLOTS):
				if self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_NAME_COL).isSelected():
					ch_name = self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_NAME_COL).text()
					if (ch_name == "?"):
						Warning_str = "Operation can't be performed"
						Reason_str = "Can't turn OFF LV for slot "+str(row)+ " beacause LV ch. name is UNKNOWN"
						if not BI_Action:
							self.Request_msg.emit(Warning_str,Reason_str)
						self.last_op_ok= False
						return
					HV_defined = True if self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_NAME_COL).text() != "?" else False	
					if (not switch) and  HV_defined and (self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_STAT_COL).text() != "OFF"):  # attempt to power down LV with HV not off
						Warning_str = "Operation can't be performed"
						Reason_str = "Can't turn OFF LV for slot "+str(row)+ " beacause HV is ON or UNKNOWN"
						if not BI_Action:
							self.Request_msg.emit(Warning_str,Reason_str)
						self.last_op_ok= False
						return
					Channel_list.append(ch_name)
				
		self.logger.info("WORKER: Setting LV "+power+ " for ch " +str(Channel_list))
		for channel in Channel_list:
			self.SendCAENControllerCmd("Turn"+power+",PowerSupplyId:caen,ChannelId:"+channel)	

	@pyqtSlot(bool)	
	def Ctrl_PowerHV_Cmd(self,switch,Channel_list=[],BI_Action=False):
		self.last_op_ok= True
		if not BI_Action:
			Channel_list.clear()
		power = "On" if switch else "Off"
		if not (self.SharedDict["CAEN_updated"] and self.SharedDict["FNALBox_updated"]):
			Warning_str = "Operation can't be performed"
			Reason_str = "CAEN and/or FNAL infos are not updated"
			if not BI_Action:
				self.Request_msg.emit(Warning_str,Reason_str)
			self.last_op_ok= False
			return
		if not (self.SharedDict["Ctrl_StatusDoor"].text() == "CLOSED"):
			Warning_str = "Operation can't be performed"
			Reason_str = "BurnIn door is NOT CLOSED"
			if not BI_Action:
				self.Request_msg.emit(Warning_str,Reason_str)
			self.last_op_ok= False
			return
		
		if len(Channel_list)==0:
			for row in range(NUM_BI_SLOTS):
				if self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_NAME_COL).isSelected():
					ch_name = self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_NAME_COL).text() 
					if (ch_name == "?"):
						Warning_str = "Operation can't be performed"
						Reason_str = "Can't turn OFF HV for slot "+str(row)+ " beacause HV ch. name is UNKNOWN"
						if not BI_Action:
							self.Request_msg.emit(Warning_str,Reason_str)
						self.last_op_ok= False
						return
					if (switch) and (self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_STAT_COL).text() != "ON"):  # attempt to power up HV with LV not on
						Warning_str = "Operation can't be performed"
						Reason_str = "Can't turn OFF HV for slot "+str(row)+ " beacause LV is OFF or UNKNOWN"
						if not BI_Action:
							self.Request_msg.emit(Warning_str,Reason_str)
						self.last_op_ok= False
						return
					Channel_list.append(ch_name)
				
		self.logger.info("WORKER: Setting HV "+power+ " for ch " +str(Channel_list))
		for channel in Channel_list:
			self.SendCAENControllerCmd("Turn"+power+",PowerSupplyId:caen,ChannelId:"+channel)
	

	@pyqtSlot(str)	
	def Ctrl_VSet_Cmd(self,VType,Channel_list=[],NewValue_list=[], BI_Action=False):
		self.last_op_ok= True
		if not BI_Action:
			Channel_list.clear()
			NewValue_list.clear()
	
		if VType != "LV" and VType != "HV":
			self.logger.error("WORKER: Received unknow Voltage type string ")
			return
			
		ColOffset = CTRLTABLE_LV_NAME_COL if VType=="LV" else CTRLTABLE_HV_NAME_COL;
		if not (self.SharedDict["CAEN_updated"]):
			Warning_str = "Operation can't be performed"
			Reason_str = "CAEN infos are not updated"
			if not BI_Action:
				self.Request_msg.emit(Warning_str,Reason_str)
			self.last_op_ok= False
			return
		if len(Channel_list) != len(NewValue_list):
			Warning_str = "Operation can't be performed"
			Reason_str = "Provided ch list and value list doesn not match in length"
			if not BI_Action:
				self.Request_msg.emit(Warning_str,Reason_str)
			self.last_op_ok= False
			return
			
		if len(Channel_list)==0:
			for row in range(NUM_BI_SLOTS):
				if self.SharedDict["CAEN_table"].item(row,ColOffset).isSelected():
					ch_name = self.SharedDict["CAEN_table"].item(row,ColOffset).text() 
					if (ch_name == "?"):
						Warning_str = "Operation can't be performed"
						Reason_str = "Can't set LV for  slot "+str(row)+ " beacause LV ch. name is UNKNOWN"
						if not BI_Action:
							self.Request_msg.emit(Warning_str,Reason_str)
						self.last_op_ok= False
						return
					if (self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_VSET_COL+ColOffset).text() == "?"):  # Unknown HV set
						Warning_str = "Operation can't be performed"
						Reason_str = "Can't set LV for  slot "+str(row)+ " beacause current setpoint is UNKNOWN"
						if not BI_Action:
							self.Request_msg.emit(Warning_str,Reason_str)
						self.last_op_ok= False
						return
					self.SharedDict["WaitInput"]=True
					Request_str="New " +VType+ " Slot "+str(row)
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

	@pyqtSlot(dict)			
	def BI_Start_Cmd(self,BI_Options):
		self.logger.info("Starting BurnIN...")
		
			
	
		TempTolerance= BI_TEMP_TOLERANCE
		LowTemp				= BI_Options["LowTemp"]
		TempRampOffset		= BI_Options["UnderRamp"]
		TempMantainOffset	= BI_Options["UnderKeep"]
		HighTemp			= BI_Options["HighTemp"]
		NCycles				= BI_Options["NCycles"]
		
		self.SharedDict["BI_Active"]=True
		
		
			
			
		if not (self.SharedDict["CAEN_updated"] and self.SharedDict["FNALBox_updated"] and self.SharedDict["Julabo_updated"]):
			self.BI_Abort("CAEN/FNAL/JULABO infos are not updated")
			return
		if not (self.SharedDict["Ctrl_StatusDoor"].text() == "CLOSED"):
			self.BI_Abort("DOOR is not closed!")
			return
		self.logger.info("BurnIn test started...")
		
		LV_Channel_list=[]
		HV_Channel_list=[]
		Slot_list=[]
		
		for row in range(NUM_BI_SLOTS):
			LV_ch_name = self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_NAME_COL).text()
			HV_ch_name = self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_NAME_COL).text() 
			if (LV_ch_name != "?" and HV_ch_name != "?" ):
				LV_Channel_list.append(LV_ch_name)
				HV_Channel_list.append(HV_ch_name)
				Slot_list.append(row)

		
		self.logger.info("BurnIn test active slots: "+str(Slot_list))
		self.logger.info("BurnIn test HV names: "+str(HV_Channel_list))
		self.logger.info("BurnIn test LV names: "+str(LV_Channel_list))			   
		
		BI_Action=True
		
		#lock magnet
		if not self.BI_Action(self.Ctrl_SetLock_Cmd,True,BI_Action):
			return
			
		#start high flow	
		if not self.BI_Action(self.Ctrl_SetHighFlow_Cmd,True,BI_Action):
			return
			
		#sel SP	
		if not self.BI_Action(self.Ctrl_SelSp_Cmd,0,BI_Action):
			return
				
		#start JULABO	
		if not self.BI_Action(self.Ctrl_PowerJulabo_Cmd,True,BI_Action):
			return
		
		##start LV
		if not self.BI_Action(self.Ctrl_PowerLV_Cmd,True,LV_Channel_list,BI_Action):
			return
		time.sleep(BI_SLEEP_AFTER_VSET)
		
		#check all LVs are ON
		for row in Slot_list:
			if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_STAT_COL).text()!="ON"):
				self.BI_Abort("BI aborted: some LVs was not turned ON")
				return
		
		#start HV
		if not self.BI_Action(self.Ctrl_PowerHV_Cmd,True,HV_Channel_list,BI_Action):
			return
		
		time.sleep(BI_SLEEP_AFTER_VSET)
		#check all HVs are ON
		for row in Slot_list:
			if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_STAT_COL).text()!="ON"):
				self.BI_Abort("BI aborted: some HVs was not turned ON")
				return
			
			
		for cycle in range (NCycles):
			self.logger.info("BI: starting cycle "+str(cycle+1) + " of "+str(NCycles))
		
			# ramp down
			self.logger.info("BI: runmping down...")
			if not self.BI_Action(self.BI_GoLowTemp,BI_Options,BI_Action):
				return
			
			#do test here...
			self.logger.info("BI: keep temperature ....")
			time.sleep(120)  # test dummy
			
			
			self.logger.info("BI: going to high temp")
			if not self.BI_Action(self.Ctrl_SetSp_Cmd,0,HighTemp):
				return
				
			while (abs(float(self.SharedDict["LastFNALBoxTemp0"].text())-HighTemp) > TempTolerance):
				if self.SharedDict["BI_StopRequest"]:
					self.BI_Abort("BI aborted: user request")
					return	
				if not (self.SharedDict["CAEN_updated"] and self.SharedDict["FNALBox_updated"] and self.SharedDict["Julabo_updated"]):
					self.BI_Abort("CAEN/FNAL/JULABO infos are not updated")
					return
				time.sleep(BI_SLEEP_AFTER_TEMP_CHECK)
				
			
			self.logger.info("BI: testing (DUMMY)")
			time.sleep(120)  # test dummy
			#do test here...
			
			self.logger.info("BI: ended cycle "+str(cycle+1) + " of "+str(NCycles))
		#stop HV
		if not self.BI_Action(self.Ctrl_PowerHV_Cmd,False,HV_Channel_list,BI_Action):
			return
		time.sleep(BI_SLEEP_AFTER_VSET)
		#check HV stop
		for row in Slot_list:
			if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_STAT_COL).text()!="OFF"):
				self.BI_Abort("BI aborted: some LVs was not turned OFF")
				return
			
		
		#stop LV
		if not self.BI_Action(self.Ctrl_PowerLV_Cmd,False,LV_Channel_list,BI_Action):
			return
		time.sleep(BI_SLEEP_AFTER_VSET)
		#check LV stop	
		for row in Slot_list:
			if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_STAT_COL).text()!="OFF"):
				self.BI_Abort("BI aborted: some HVs was not turned OFF")
				return
				
		#start JULABO	
		if not self.BI_Action(self.Ctrl_PowerJulabo_Cmd,False,BI_Action):
			return
		
		self.logger.info("BurnIn test COMPLETED SUCCESFULLY!")
		self.SharedDict["BI_Active"]=False
		self.SharedDict["BI_StopRequest"]=False
		self.BI_terminated.emit()
		
	def BI_Abort(self,Reason_str):
	
			Warning_str = "BURN IN test failed"
			self.Request_msg.emit(Warning_str,Reason_str)
			self.SharedDict["BI_Active"]=False
			self.SharedDict["BI_StopRequest"]=False
			self.BI_terminated.emit()
		
	
		
	def BI_Action(self,Action,*args):
		retry=BI_ACTION_RETRIES
		while retry:
			Action(*args)
			if not (self.last_op_ok):
				self.logger.warning("BI: failed to do action...new try in 10 sec")
				time.sleep(BI_ACTION_RETRY_SLEEP)
				retry=retry-1
			else:
				return True
		self.BI_Abort("BI: failed to do action (3 times)...aborting")
		return False

	def BI_GoLowTemp(self,BI_Options):
	
		TempTolerance		= BI_TEMP_TOLERANCE
		LowTemp				= test_option["LowTemp"]
		TempRampOffset		= test_option["UnderRamp"]
		TempMantainOffset	= test_option["UnderKeep"]
		
		last_step=False
		self.last_op_ok= True
		BI_Action=True
		nextTemp = 0.0
		
		while (not last_step):
			try:
				dewPoint = float(self.SharedDict["Ctrl_IntDewPoint"].text())
			except Exception as e:
				self.logger.error(e)
				self.last_op_ok= False
				return
			
			if (lowtemp-TempRampOffset> dewPoint):
				nextTemp = LowTemp-TempRampOffset
				self.logger.info("BI: target low temp OK...")
				last_step = True
			else:
				nextTemp = dewPoint
				self.logger.info("BI: target low temp below dew point, going to dewPoint...")
			
			if not self.BI_Action(self.Ctrl_SetSp_Cmd,0,nextTemp,BI_Action):
				self.last_op_ok= False
				return	
				
			while (abs(float(self.SharedDict["LastFNALBoxTemp0"].text())-LowTemp) > TempTolerance):
				if self.SharedDict["BI_StopRequest"]:
					self.BI_Abort("BI aborted: user request")
					return	
				if not (self.SharedDict["CAEN_updated"] and self.SharedDict["FNALBox_updated"] and self.SharedDict["Julabo_updated"]):
					self.BI_Abort("CAEN/FNAL/JULABO infos are not updated")
					return
				time.sleep(10)	
			
			
			
		# set target temperature mantain
		self.logger.info("BI: keep temperature ....")
		if not self.BI_Action(self.Ctrl_SetSp_Cmd,0,LowTemp-TempMantainOffset,BI_Action):
			self.last_op_ok= False
			return