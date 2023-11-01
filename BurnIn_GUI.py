import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from PyQt5.QtCore import QThread, pyqtSlot, pyqtSignal


from BurnIn_TCP import *

from BurnIn_Worker import *
from BurnIn_Monitor import *


class BurnIn_GUI(QtWidgets.QMainWindow):

	
	SendJulaboCmd_sig = pyqtSignal(str)
	SendFNALBoxCmd_sig = pyqtSignal(str)


	Ctrl_SetSp_sig = pyqtSignal(int,float)
	Ctrl_SelSp_sig = pyqtSignal(int)
	Ctrl_PowerJulabo_sig = pyqtSignal(bool)
	Ctrl_SetHighFlow_sig = pyqtSignal(bool)
	Ctrl_SetLock_sig = pyqtSignal(bool)
	


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
		self.MonitorTags = {}
		self.MonitorTags["LastMonitor"]=self.LastMonitor_tag
		self.MonitorTags["MQTTConn"]=self.MQTTConn_tag
		self.MonitorTags["JULABOConn"]=self.JULABOConn_tag
		self.MonitorTags["FNALConn"]=self.FNALConn_tag
		self.MonitorTags["LastMQTTCAENMsgTS"]=self.LastMQTTCAENMsgTS_tag
		self.MonitorTags["LastMQTTM5MsgTS"]=self.LastMQTTM5MsgTS_tag
		self.MonitorTags["LastM5Temp"]=self.LastM5Temp_tag
		self.MonitorTags["LastM5Humi"]=self.LastM5Humi_tag
		self.MonitorTags["LastM5Pres"]=self.LastM5Pres_tag
		self.MonitorTags["LastM5DP"]=self.LastM5DP_tag
		self.MonitorTags["LastJulaboMsgTS"]=self.LastJulaboMsgTS_tag
		self.MonitorTags["LastJulaboStatus"]=self.LastJulaboStatus_tag
		self.MonitorTags["LastJulaboSP1"]=self.LastJulaboSP1_tag
		self.MonitorTags["LastJulaboSP2"]=self.LastJulaboSP2_tag
		self.MonitorTags["LastJulaboSP3"]=self.LastJulaboSP3_tag
		self.MonitorTags["LastJulaboBT"]=self.LastJulaboBT_tag
		self.MonitorTags["LastJulaboHP"]=self.LastJulaboHP_tag
		self.MonitorTags["LastJulaboTSP"]=self.LastJulaboTSP_tag
		self.MonitorTags["LastFNALBoxMsgTS"]=self.LastFNALBoxMsgTS_tag
		self.MonitorTags["LastFNALBoxTemp0"]=self.LastFNALBoxTemp0_tag
		self.MonitorTags["LastFNALBoxTemp1"]=self.LastFNALBoxTemp1_tag
		self.MonitorTags["LastFNALBoxDP"]=self.LastFNALBoxDP_tag
		
		
		self.MonitorTags["CH00_ID"]=self.CH00_ID
		self.MonitorTags["CH01_ID"]=self.CH01_ID
		self.MonitorTags["CH02_ID"]=self.CH02_ID
		self.MonitorTags["CH03_ID"]=self.CH03_ID
		self.MonitorTags["CH04_ID"]=self.CH04_ID
		self.MonitorTags["CH05_ID"]=self.CH05_ID
		self.MonitorTags["CH06_ID"]=self.CH06_ID
		self.MonitorTags["CH00_ST"]=self.CH00_ST
		self.MonitorTags["CH01_ST"]=self.CH01_ST
		self.MonitorTags["CH02_ST"]=self.CH02_ST
		self.MonitorTags["CH03_ST"]=self.CH03_ST
		self.MonitorTags["CH04_ST"]=self.CH04_ST
		self.MonitorTags["CH05_ST"]=self.CH05_ST
		self.MonitorTags["CH06_ST"]=self.CH06_ST
		self.MonitorTags["CH00_V"]=self.CH00_V
		self.MonitorTags["CH01_V"]=self.CH01_V
		self.MonitorTags["CH02_V"]=self.CH02_V
		self.MonitorTags["CH03_V"]=self.CH03_V
		self.MonitorTags["CH04_V"]=self.CH04_V
		self.MonitorTags["CH05_V"]=self.CH05_V
		self.MonitorTags["CH06_V"]=self.CH06_V
		self.MonitorTags["CH00_I"]=self.CH00_I
		self.MonitorTags["CH01_I"]=self.CH01_I
		self.MonitorTags["CH02_I"]=self.CH02_I
		self.MonitorTags["CH03_I"]=self.CH03_I
		self.MonitorTags["CH04_I"]=self.CH04_I
		self.MonitorTags["CH05_I"]=self.CH05_I
		self.MonitorTags["CH06_I"]=self.CH06_I
		
		self.MonitorTags["Ctrl_Sp1"]=self.Ctrl_Sp1_tag
		self.MonitorTags["Ctrl_Sp2"]=self.Ctrl_Sp2_tag
		self.MonitorTags["Ctrl_Sp3"]=self.Ctrl_Sp3_tag
		self.MonitorTags["Ctrl_TSp"]=self.Ctrl_TSp_tag
		self.MonitorTags["Ctrl_StatusJulabo"]=self.Ctrl_StatusJulabo_tag
		self.MonitorTags["Ctrl_TargetTemp"]=self.Ctrl_TargetTemp_tag
		self.MonitorTags["Ctrl_IntDewPoint"]=self.Ctrl_IntDewPoint_tag
		self.MonitorTags["Ctrl_ExtDewPoint"]=self.Ctrl_ExtDewPoint_tag
		
		self.MonitorTags["Ctrl_StatusFlow"]=self.Ctrl_StatusFlow_tag
		self.MonitorTags["Ctrl_StatusLock"]=self.Ctrl_StatusLock_tag
		
		
		self.MonitorTags["M5_updated"]=False
		self.MonitorTags["Julabo_updated"]=False
		self.MonitorTags["FNALBox_updated"]=False
		self.MonitorTags["CAEN_updated"]=False

		
		
		# start monitoring function in QThread
		self.MonitorThread = QThread()
		self.Monitor = BurnIn_Monitor(self.configDict,self.logger, self.MonitorTags, self.Julabo, self.FNALBox)
		self.Monitor.moveToThread(self.MonitorThread)
		self.MonitorThread.started.connect(self.Monitor.run)
		self.MonitorThread.start()	
		
		
		# start GUI worker in QThread
		self.WorkerThread = QThread()
		self.Worker = BurnIn_Worker(self.configDict,self.logger, self.MonitorTags, self.Julabo, self.FNALBox)
		self.Worker.moveToThread(self.WorkerThread)
		self.WorkerThread.start()	
		
		#connecting local slots
		
		self.JulaboTestCmd_btn.clicked.connect(self.SendJulaboCmd)	
		self.FNALBoxTestCmd_btn.clicked.connect(self.SendFNALBoxCmd)
		self.Ctrl_SetSp1_btn.clicked.connect(lambda : self.Ctrl_SetSp_Cmd(0,self.Ctrl_ValSp1_dsb.value()))
		self.Ctrl_SetSp2_btn.clicked.connect(lambda : self.Ctrl_SetSp_Cmd(1,self.Ctrl_ValSp2_dsb.value()))
		self.Ctrl_SetSp3_btn.clicked.connect(lambda : self.Ctrl_SetSp_Cmd(2,self.Ctrl_ValSp3_dsb.value()))
		self.Ctrl_SelSp1_btn.clicked.connect(lambda : self.Ctrl_SelSp_Cmd(0))
		self.Ctrl_SelSp2_btn.clicked.connect(lambda : self.Ctrl_SelSp_Cmd(1))
		self.Ctrl_SelSp3_btn.clicked.connect(lambda : self.Ctrl_SelSp_Cmd(2))
		self.Ctrl_SetLowFlow_btn.clicked.connect(lambda : self.Ctrl_SetHighFlow_Cmd(False))
		self.Ctrl_SetHighFlow_btn.clicked.connect(lambda : self.Ctrl_SetHighFlow_Cmd(True))
		self.Ctrl_SetLock_btn.clicked.connect    (lambda : self.Ctrl_SetLock_Cmd(True))
		self.Ctrl_SetUnlock_btn.clicked.connect  (lambda : self.Ctrl_SetLock_Cmd(False))
		self.Ctrl_StartJulabo_btn.clicked.connect(lambda : self.Ctrl_PowerJulabo_Cmd(True))
		self.Ctrl_StopJulabo_btn.clicked.connect (lambda : self.Ctrl_PowerJulabo_Cmd(False))
		
		self.actionExit.triggered.connect(self.close)
		self.actionExpert.triggered.connect(self.expert)
		
		#connecting worker slots
		self.SendJulaboCmd_sig.connect(self.Worker.SendJulaboCmd)
		self.SendFNALBoxCmd_sig.connect(self.Worker.SendFNALBoxCmd)
		
		self.Ctrl_SelSp_sig.connect(self.Worker.Ctrl_SelSp_Cmd)
		self.Ctrl_SetSp_sig.connect(self.Worker.Ctrl_SetSp_Cmd)
		self.Ctrl_PowerJulabo_sig.connect(self.Worker.Ctrl_PowerJulabo_Cmd)
		self.Ctrl_SetLock_sig.connect(self.Worker.Ctrl_SetLock_Cmd)
		self.Ctrl_SetHighFlow_sig.connect(self.Worker.Ctrl_SetHighFlow_Cmd)
		
		
		
		self.Worker.Request_msg.connect(self.Show_msg)
		
		
		self.statusBar().showMessage("System ready")
		
	def SendJulaboCmd(self):
		self.SendJulaboCmd_sig.emit(self.JulaboTestCmd_line.text())
		
	def SendFNALBoxCmd(self):
		self.SendFNALBoxCmd_sig.emit(self.FNALBoxTestCmd_line.text())
	
	def Ctrl_SetSp_Cmd(self,Sp_ID,value):
		self.Ctrl_SetSp_sig.emit(Sp_ID,value)
	
	def Ctrl_SelSp_Cmd(self,Sp_ID):
		self.Ctrl_SelSp_sig.emit(Sp_ID)
	
	def Ctrl_PowerJulabo_Cmd(self,switch):
		self.Ctrl_PowerJulabo_sig.emit(switch)
	
	def Ctrl_SetHighFlow_Cmd(self,switch):
		self.Ctrl_SetHighFlow_sig.emit(switch)
	
	def Ctrl_SetLock_Cmd(self,switch):
		self.Ctrl_SetLock_sig.emit(switch)
		
	@pyqtSlot(str,str)
	def Show_msg(self,warn_msg,rsn_msg):
		self.logger.warning(warn_msg)
		self.logger.warning(rsn_msg)
		msg = QMessageBox()
		msg.setWindowTitle("Operation warning")
		msg.setText(warn_msg)
		msg.setIcon(QMessageBox.Warning)
		msg.setInformativeText(rsn_msg)
		msg.exec()
		
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
