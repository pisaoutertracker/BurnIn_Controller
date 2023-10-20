import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject, pyqtSlot
import time


class BurnIn_Worker(QObject):

	def __init__(self,configDict,logger, Julabo):
	
		super(BurnIn_Worker,self).__init__();
		self.configDict=configDict
		self.logger = logger
		self.Julabo = Julabo
		
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