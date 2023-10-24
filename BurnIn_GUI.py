import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from PyQt5.QtCore import QThread, pyqtSlot, pyqtSignal


from BurnIn_TCP import *

from BurnIn_Worker import *
from BurnIn_Monitor import *


class BurnIn_GUI(QtWidgets.QMainWindow):

	
	SendJulaboCmd_sig = pyqtSignal(str)
	SendFNALBoxCmd_sig = pyqtSignal(str)

	def __init__(self,configDict,logger):
		super(BurnIn_GUI,self).__init__()
		self.is_expert=False
		self.logger=logger
		self.configDict=configDict
		
		
		self.initUI()
		
		
	def initUI(self):
	
		uic.loadUi('GUI.ui', self) # Load the .ui file
		self.show() # Show the GUI
		
		self.Julabo = BurnIn_TCP(self.configDict,self.logger,"Julabo")
		self.FNALBox = BurnIn_TCP(self.configDict,self.logger,"FNALBox")
		
		#packing monitor tag
		self.MonitorTags = []
		self.MonitorTags.append(self.LastMonitor_tag)
		self.MonitorTags.append(self.MQTTConn_tag)
		self.MonitorTags.append(self.JULABOConn_tag)
		self.MonitorTags.append(self.FNALConn_tag)
		self.MonitorTags.append(self.LastMQTTMsgTS_tag)
		self.MonitorTags.append(self.LastMQTTMsg_tag)
		self.MonitorTags.append(self.LastMQTTSource_tag)
		self.MonitorTags.append(self.LastJulaboMsgTS_tag)
		self.MonitorTags.append(self.LastJulaboStatus_tag)
		self.MonitorTags.append(self.LastJulaboSP1_tag)
		self.MonitorTags.append(self.LastFNALBoxMsgTS_tag)


		
		
		# start monitoring function in QThread
		self.MonitorThread = QThread()
		self.Monitor = BurnIn_Monitor(self.configDict,self.logger, self.MonitorTags, self.Julabo, self.FNALBox)
		self.Monitor.moveToThread(self.MonitorThread)
		self.MonitorThread.started.connect(self.Monitor.run)
		self.MonitorThread.start()	
		
		
		# start GUI worker in QThread
		self.WorkerThread = QThread()
		self.Worker = BurnIn_Worker(self.configDict,self.logger, self.Julabo, self.FNALBox)
		self.Worker.moveToThread(self.WorkerThread)
		self.WorkerThread.start()	
		
		self.SendJulaboCmd_sig.connect(self.Worker.SendJulaboCmd)
		self.JulaboTestCmd_btn.clicked.connect(self.SendJulaboCmd)	
		self.SendFNALBoxCmd_sig.connect(self.Worker.SendFNALBoxCmd)
		self.FNALBoxTestCmd_btn.clicked.connect(self.SendFNALBoxCmd)	
		#connecting slots
		self.actionExit.triggered.connect(self.close)
		self.actionExpert.triggered.connect(self.expert)
		self.statusBar().showMessage("System ready")
		
	def SendJulaboCmd(self):
		self.SendJulaboCmd_sig.emit(self.JulaboTestCmd_line.text())
		
	def SendFNALBoxCmd(self):
		self.SendFNALBoxCmd_sig.emit(self.FNALBoxTestCmd_line.text())
		
		
	def expert(self):
		psw, ok = QtWidgets.QInputDialog.getText(None, "Expert mode", "Password?", QtWidgets.QLineEdit.Password)
		if psw=='1234' and ok:
			self.logger.info("Expert mode activated")
			self.statusBar().showMessage("Expert mode activated")
			self.is_expert=True
		

if __name__== '__main__':
	
	app = QtWidgets.QApplication(sys.argv)
	BurnIn_app = BurnIn_GUI(0, 0)
	sys.exit(app.exec_()) #continua esecuzione fino a che non chiudo