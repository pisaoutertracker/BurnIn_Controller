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
		self.MonitorInfo = {}
		self.MonitorInfo["LastMonitor"]=self.LastMonitor_tag
		self.MonitorInfo["MQTTConn"]=self.MQTTConn_tag
		self.MonitorInfo["JULABOConn"]=self.JULABOConn_tag
		self.MonitorInfo["FNALConn"]=self.FNALConn_tag
		self.MonitorInfo["LastMQTTCAENMsgTS"]=self.LastMQTTCAENMsgTS_tag
		self.MonitorInfo["LastMQTTM5MsgTS"]=self.LastMQTTM5MsgTS_tag
		self.MonitorInfo["LastM5Temp"]=self.LastM5Temp_tag
		self.MonitorInfo["LastM5Humi"]=self.LastM5Humi_tag
		self.MonitorInfo["LastM5Pres"]=self.LastM5Pres_tag
		self.MonitorInfo["LastM5DP"]=self.LastM5DP_tag
		self.MonitorInfo["LastJulaboMsgTS"]=self.LastJulaboMsgTS_tag
		self.MonitorInfo["LastJulaboStatus"]=self.LastJulaboStatus_tag
		self.MonitorInfo["LastJulaboSP1"]=self.LastJulaboSP1_tag
		self.MonitorInfo["LastJulaboSP2"]=self.LastJulaboSP2_tag
		self.MonitorInfo["LastJulaboSP3"]=self.LastJulaboSP3_tag
		self.MonitorInfo["LastJulaboBT"]=self.LastJulaboBT_tag
		self.MonitorInfo["LastJulaboHP"]=self.LastJulaboHP_tag
		self.MonitorInfo["LastJulaboTSP"]=self.LastJulaboTSP_tag
		self.MonitorInfo["LastFNALBoxMsgTS"]=self.LastFNALBoxMsgTS_tag
		self.MonitorInfo["LastFNALBoxTemp0"]=self.LastFNALBoxTemp0_tag
		self.MonitorInfo["LastFNALBoxTemp1"]=self.LastFNALBoxTemp1_tag
		self.MonitorInfo["LastFNALBoxDP"]=self.LastFNALBoxDP_tag
		
		
		self.MonitorInfo["CH00_ID"]=self.CH00_ID
		self.MonitorInfo["CH01_ID"]=self.CH01_ID
		self.MonitorInfo["CH02_ID"]=self.CH02_ID
		self.MonitorInfo["CH03_ID"]=self.CH03_ID
		self.MonitorInfo["CH04_ID"]=self.CH04_ID
		self.MonitorInfo["CH05_ID"]=self.CH05_ID
		self.MonitorInfo["CH06_ID"]=self.CH06_ID
		self.MonitorInfo["CH00_ST"]=self.CH00_ST
		self.MonitorInfo["CH01_ST"]=self.CH01_ST
		self.MonitorInfo["CH02_ST"]=self.CH02_ST
		self.MonitorInfo["CH03_ST"]=self.CH03_ST
		self.MonitorInfo["CH04_ST"]=self.CH04_ST
		self.MonitorInfo["CH05_ST"]=self.CH05_ST
		self.MonitorInfo["CH06_ST"]=self.CH06_ST
		self.MonitorInfo["CH00_V"]=self.CH00_V
		self.MonitorInfo["CH01_V"]=self.CH01_V
		self.MonitorInfo["CH02_V"]=self.CH02_V
		self.MonitorInfo["CH03_V"]=self.CH03_V
		self.MonitorInfo["CH04_V"]=self.CH04_V
		self.MonitorInfo["CH05_V"]=self.CH05_V
		self.MonitorInfo["CH06_V"]=self.CH06_V
		self.MonitorInfo["CH00_I"]=self.CH00_I
		self.MonitorInfo["CH01_I"]=self.CH01_I
		self.MonitorInfo["CH02_I"]=self.CH02_I
		self.MonitorInfo["CH03_I"]=self.CH03_I
		self.MonitorInfo["CH04_I"]=self.CH04_I
		self.MonitorInfo["CH05_I"]=self.CH05_I
		self.MonitorInfo["CH06_I"]=self.CH06_I
		
		
		


		
		
		# start monitoring function in QThread
		self.MonitorThread = QThread()
		self.Monitor = BurnIn_Monitor(self.configDict,self.logger, self.MonitorInfo, self.Julabo, self.FNALBox)
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