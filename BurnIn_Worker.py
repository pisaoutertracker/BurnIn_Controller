import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject, pyqtSlot
import time


class BurnIn_Worker(QObject):

	def __init__(self,configDict,logger, Julabo, FNALBox):
	
		super(BurnIn_Worker,self).__init__();
		self.configDict=configDict
		self.logger = logger
		self.Julabo = Julabo
		self.FNALBox = FNALBox
		
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
			self.logger.info(self.FNALBox.receive())
		self.FNALBox.lock.release()