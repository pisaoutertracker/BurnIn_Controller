import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject
import time


class BurnIn_Worker(QObject):

	def __init__(self,configDict,logger):
	
		super(BurnIn_Worker,self).__init__();
		self.configDict=configDict
		self.logger = logger
		self.logger.info("Worker class initialized")