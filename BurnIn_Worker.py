import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
import time


class BurnIn_Worker(QObject):

	Request_msg = pyqtSignal(str,str)
	
	def __init__(self,configDict,logger, MonitorTags, Julabo, FNALBox):
	
		super(BurnIn_Worker,self).__init__();
		self.configDict=configDict
		self.logger = logger
		self.Julabo = Julabo
		self.FNALBox = FNALBox
		self.MonitorTags = MonitorTags
		self.MonitorTags = MonitorTags
		
		self.logger.info("Worker class initialized")
	
	@pyqtSlot(str)
	def SendJulaboCmd(self,cmd):
		self.Julabo.lock.acquire()
		self.logger.info("Sending Julabo cmd "+cmd)
		if not self.Julabo.is_connected :
			self.Julabo.connect()
		if self.Julabo.is_connected :
			self.Julabo.sendTCP(cmd)
			self.logger.info(self.Julabo.receive())
		self.Julabo.lock.release()
	
	@pyqtSlot(str)
	def SendFNALBoxCmd(self,cmd):
		self.FNALBox.lock.acquire()
		self.logger.info("Sending FNALBox cmd "+cmd)
		if not self.FNALBox.is_connected :
			self.FNALBox.connect()
		if self.FNALBox.is_connected :
			self.FNALBox.sendTCP(cmd)
			time.sleep(0.250)
			self.logger.info(self.FNALBox.receive())
		self.FNALBox.lock.release()
	
	@pyqtSlot(int)	
	def Ctrl_SelSp_Cmd(self,Sp_id):
		self.logger.info("WORKER: Selecting JULABO Sp"+str(Sp_id+1))
		if not (self.MonitorTags["Julabo_updated"] and self.MonitorTags["FNALBox_updated"]):
			Warning_str = "Operation can't be performed"
			Reason_str = "Julabo and/or FNAL box info are not updated"
			self.Request_msg.emit(Warning_str,Reason_str)
			return
		else:	
			if (self.MonitorTags["Ctrl_StatusJulabo"].text().find("START") != -1):
				targetT = -100.0
				if Sp_id == 0 :
					targetT = float(self.MonitorTags["Ctrl_Sp1"].text())
				elif Sp_id == 1 :
					targetT = float(self.MonitorTags["Ctrl_Sp2"].text())
				elif Sp_id == 2 :
					targetT = float(self.MonitorTags["Ctrl_Sp3"].text())

				if targetT  < float(self.MonitorTags["Ctrl_IntDewPoint"].text()):
					Warning_str = "Operation can't be performed"
					Reason_str = "Set point is configured with a temperature below internal dew point"
					self.logger.warning(Warning_str)
					self.logger.warning(Reason_str)
					self.Request_msg.emit(Warning_str,Reason_str)
					return

			self.Julabo.lock.acquire()
			self.logger.debug("WORKER: Sending Julabo cmd" )
			if not self.Julabo.is_connected :
				self.Julabo.connect()
			if self.Julabo.is_connected :
				try:
					self.Julabo.sendTCP("out_mode_01 "+str(Sp_id))
					self.logger.info("WORKER: JULABO cmd sent")
				except Exception as e:
					self.logger.error(e)	
						
			self.Julabo.lock.release()
			
	
	@pyqtSlot(int,float)	
	def Ctrl_SetSp_Cmd(self,Sp_id,value):
		self.logger.info("WORKER: Setting JULABO Sp"+str(Sp_id+1)+ " to " +str(value))
		if not (self.MonitorTags["Julabo_updated"] and self.MonitorTags["FNALBox_updated"]):
			Warning_str = "Operation can't be performed"
			Reason_str = "Julabo and/or FNAL box info are not updated"
			self.Request_msg.emit(Warning_str,Reason_str)
			return
		else:	
			if (self.MonitorTags["Ctrl_StatusJulabo"].text().find("START") != -1):
				Sp_actual = int(self.MonitorTags["Ctrl_TSp"].text())-1
				print() 
				if Sp_actual==Sp_id and  value  < float(self.MonitorTags["Ctrl_IntDewPoint"].text()):
					Warning_str = "Operation can't be performed"
					Reason_str = "Attempting to set target temperature of the active set point below internal dew point"
					self.logger.warning(Warning_str)
					self.logger.warning(Reason_str)
					self.Request_msg.emit(Warning_str,Reason_str)
					return

			self.Julabo.lock.acquire()
			self.logger.debug("WORKER: Sending Julabo cmd" )
			if not self.Julabo.is_connected :
				self.Julabo.connect()
			if self.Julabo.is_connected :
				try:
					self.Julabo.sendTCP("out_sp_0"+str(Sp_id)+" "+str(value))
					self.logger.info("WORKER: JULABO cmd sent")
				except Exception as e:
					self.logger.error(e)	
						
			self.Julabo.lock.release()
		
	@pyqtSlot(bool)	
	def Ctrl_PowerJulabo_Cmd(self,switch):
		
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
				except Exception as e:
					self.logger.error(e)	
						
			self.Julabo.lock.release()
		else:	
			self.logger.info("WORKER: Powering Julabo ON")
			if not (self.MonitorTags["Julabo_updated"] and self.MonitorTags["FNALBox_updated"]):
				Warning_str = "Operation can't be performed"
				Reason_str = "Julabo and/or FNAL box info are not updated"
				self.Request_msg.emit(Warning_str,Reason_str)
				return
			else:	
				if float(self.MonitorTags["Ctrl_TargetTemp"].text())< float(self.MonitorTags["Ctrl_IntDewPoint"].text()):
					Warning_str = "Operation can't be performed"
					Reason_str = "Attempting to start unit with target temperature below internal dew point"
					self.logger.warning(Warning_str)
					self.logger.warning(Reason_str)
					self.Request_msg.emit(Warning_str,Reason_str)
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
						except Exception as e:
							self.logger.error(e)	
					
					self.Julabo.lock.release()

					
		
	@pyqtSlot(bool)	
	def Ctrl_SetLock_Cmd(self,switch):
		
		lock = "LOCKED" if switch else "UNLOCK"
		cmd = "[5011]" if switch else "[5010]"

		self.logger.info("WORKER: Setting door magnet to: "+lock)
		self.FNALBox.lock.acquire()
		self.logger.debug("WORKER: Sending FNAL Box cmd" )
		if not self.FNALBox.is_connected :
			self.FNALBox.connect()
		if self.FNALBox.is_connected :
			try:
				self.FNALBox.sendTCP(cmd)
				self.logger.info("WORKER: FNAL Box cmd sent: " + cmd)
				time.sleep(0.250)
				reply = self.FNALBox.receive()
				if reply[-3:]=="[*]":
					self.MonitorTags["Ctrl_StatusLock"].setText(lock)
					self.logger.info("WORKER: Done")
				else:
					self.MonitorTags["Ctrl_StatusLock"].setText("?")
					self.logger.error("WORKER: uncorrect reply from FNAL Box: "+reply)
			except Exception as e:
				self.logger.error(e)
				self.MonitorTags["Ctrl_StatusLock"].setText("?")	
					
		self.FNALBox.lock.release()
		
		
	@pyqtSlot(bool)	
	def Ctrl_SetHighFlow_Cmd(self,switch):
		
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
				time.sleep(0.250)
				reply = self.FNALBox.receive()
				if reply[-3:]=="[*]":
					self.MonitorTags["Ctrl_StatusFlow"].setText(flow)
					self.logger.info("WORKER: Done")
				else:
					self.MonitorTags["Ctrl_StatusFlow"].setText("?")
					self.logger.error("WORKER: uncorrect reply from FNAL Box: "+reply)
			except Exception as e:
				self.logger.error(e)
				self.MonitorTags["Ctrl_StatusFlow"].setText("?")	
					
		self.FNALBox.lock.release()

		
	
	
	
	
	
