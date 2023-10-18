import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject, pyqtSlot
import time

from Julabo import *

class BurnIn_Worker(QObject):

	def __init__(self,configDict,logger, Julabo):
	
		super(BurnIn_Worker,self).__init__();
		self.configDict=configDict
		self.logger = logger
		self.Julabo = Julabo
		
		self.logger.info("Worker class initialized")
	
	@pyqtSlot(str)
	def SendJulaboCmd(self,cmd):
		try:
			self.logger.debug("Attempting to send command to Julabo: " + cmd)
			self.Julabo.connect()
			self.Julabo.sendTCP(str(cmd))
			self.logger.debug(self.Julabo.receive())
			self.Julabo.close()
		except Exception as e:
			self.logger.error(e)