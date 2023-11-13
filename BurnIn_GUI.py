import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from PyQt5.QtCore import QThread, pyqtSlot, pyqtSignal


from BurnIn_TCP import *

from BurnIn_Worker import *
from BurnIn_Monitor import *


class BurnIn_GUI(QtWidgets.QMainWindow):

	
	SendJulaboCmd_sig = pyqtSignal(str)
	SendFNALBoxCmd_sig = pyqtSignal(str)
	SendCAENControllerCmd_sig = pyqtSignal(str)
	SendModuleTestCmd_sig = pyqtSignal(str)


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

		self.LVNames=["?"] * 10
		self.LVNames[0]="nc0"
		self.LVNames[1]="BLV08"
		self.LVNames[2]="BLV09"
		self.LVNames[3]="BLV10"

		self.HVNames=["?"] * 10
		self.HVNames[0]="HV001"
		self.HVNames[1]="HV002"
		self.HVNames[2]="HV003"
		
		self.initUI()
		
		
	def initUI(self):
	
		uic.loadUi('GUI.ui', self) # Load the .ui file
		self.show() # Show the GUI
		
		#adjust GUI table elements
		self.Ctrl_CAEN_table.item(0,0).setCheckState(QtCore.Qt.Unchecked)
		for row in range(10):
			self.Ctrl_CAEN_table.item(row+1,0).setCheckState(QtCore.Qt.Unchecked) 
			self.Ctrl_CAEN_table.setItem(row+1,1,QtWidgets.QTableWidgetItem(self.LVNames[row]))
			self.Ctrl_CAEN_table.setItem(row+1,2,QtWidgets.QTableWidgetItem("?"))
			self.Ctrl_CAEN_table.setItem(row+1,3,QtWidgets.QTableWidgetItem("?"))
			self.Ctrl_CAEN_table.setItem(row+1,4,QtWidgets.QTableWidgetItem("?"))
			self.Ctrl_CAEN_table.setItem(row+1,5,QtWidgets.QTableWidgetItem("?"))
			self.Ctrl_CAEN_table.setItem(row+1,6,QtWidgets.QTableWidgetItem(self.HVNames[row]))
			self.Ctrl_CAEN_table.setItem(row+1,7,QtWidgets.QTableWidgetItem("?"))
			self.Ctrl_CAEN_table.setItem(row+1,8,QtWidgets.QTableWidgetItem("?"))
			self.Ctrl_CAEN_table.setItem(row+1,9,QtWidgets.QTableWidgetItem("?"))
			self.Ctrl_CAEN_table.setItem(row+1,10,QtWidgets.QTableWidgetItem("?"))
		
		
		self.Julabo = BurnIn_TCP(self.configDict,self.logger,"Julabo")
		self.FNALBox = BurnIn_TCP(self.configDict,self.logger,"FNALBox")
		self.CAENController = BurnIn_TCP(self.configDict,self.logger,"CAENController")

		#for idx,name in enumerate(self.LVNames):
		#	self.Ctrl_LVCh_comboBox.addItem(name)
		#for idx,name in enumerate(self.HVNames):
		#	self.Ctrl_HVCh_comboBox.addItem(name)

		
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
		self.MonitorTags["LastFNALBoxOW0"]=self.LastFNALBoxOW0_tag
		self.MonitorTags["LastFNALBoxOW1"]=self.LastFNALBoxOW1_tag
		self.MonitorTags["LastFNALBoxOW2"]=self.LastFNALBoxOW2_tag
		self.MonitorTags["LastFNALBoxOW3"]=self.LastFNALBoxOW3_tag
		self.MonitorTags["LastFNALBoxOW4"]=self.LastFNALBoxOW4_tag
		self.MonitorTags["LastFNALBoxOW5"]=self.LastFNALBoxOW5_tag
		self.MonitorTags["LastFNALBoxOW6"]=self.LastFNALBoxOW6_tag
		self.MonitorTags["LastFNALBoxOW7"]=self.LastFNALBoxOW7_tag
		self.MonitorTags["LastFNALBoxOW8"]=self.LastFNALBoxOW8_tag
		self.MonitorTags["LastFNALBoxOW9"]=self.LastFNALBoxOW9_tag
		
		
		self.MonitorTags["LastLV00Current"]=self.LastLV00Current_tag
		self.MonitorTags["LastLV01Current"]=self.LastLV01Current_tag
		self.MonitorTags["LastLV02Current"]=self.LastLV02Current_tag
		self.MonitorTags["LastLV03Current"]=self.LastLV03Current_tag
		self.MonitorTags["LastLV04Current"]=self.LastLV04Current_tag
		self.MonitorTags["LastLV05Current"]=self.LastLV05Current_tag
		self.MonitorTags["LastLV06Current"]=self.LastLV06Current_tag
		self.MonitorTags["LastLV07Current"]=self.LastLV07Current_tag
		self.MonitorTags["LastLV08Current"]=self.LastLV08Current_tag
		self.MonitorTags["LastLV09Current"]=self.LastLV09Current_tag
		self.MonitorTags["LastLV00Voltage"]=self.LastLV00Voltage_tag
		self.MonitorTags["LastLV01Voltage"]=self.LastLV01Voltage_tag
		self.MonitorTags["LastLV02Voltage"]=self.LastLV02Voltage_tag
		self.MonitorTags["LastLV03Voltage"]=self.LastLV03Voltage_tag
		self.MonitorTags["LastLV04Voltage"]=self.LastLV04Voltage_tag
		self.MonitorTags["LastLV05Voltage"]=self.LastLV05Voltage_tag
		self.MonitorTags["LastLV06Voltage"]=self.LastLV06Voltage_tag
		self.MonitorTags["LastLV07Voltage"]=self.LastLV07Voltage_tag
		self.MonitorTags["LastLV08Voltage"]=self.LastLV08Voltage_tag
		self.MonitorTags["LastLV09Voltage"]=self.LastLV09Voltage_tag
		self.MonitorTags["LastLV00Status"]=self.LastLV00Status_tag
		self.MonitorTags["LastLV01Status"]=self.LastLV01Status_tag
		self.MonitorTags["LastLV02Status"]=self.LastLV02Status_tag
		self.MonitorTags["LastLV03Status"]=self.LastLV03Status_tag
		self.MonitorTags["LastLV04Status"]=self.LastLV04Status_tag
		self.MonitorTags["LastLV05Status"]=self.LastLV05Status_tag
		self.MonitorTags["LastLV06Status"]=self.LastLV06Status_tag
		self.MonitorTags["LastLV07Status"]=self.LastLV07Status_tag
		self.MonitorTags["LastLV08Status"]=self.LastLV08Status_tag
		self.MonitorTags["LastLV09Status"]=self.LastLV09Status_tag
		self.LV00ID_tag.setText(self.LVNames[0])
		self.LV01ID_tag.setText(self.LVNames[1])
		self.LV02ID_tag.setText(self.LVNames[2])
		self.LV03ID_tag.setText(self.LVNames[3])
		self.LV04ID_tag.setText(self.LVNames[4])
		self.LV05ID_tag.setText(self.LVNames[5])
		self.LV06ID_tag.setText(self.LVNames[6])
		self.LV07ID_tag.setText(self.LVNames[7])
		self.LV08ID_tag.setText(self.LVNames[8])
		self.LV09ID_tag.setText(self.LVNames[9])
		
		self.MonitorTags["LastHV00Current"]=self.LastHV00Current_tag
		self.MonitorTags["LastHV01Current"]=self.LastHV01Current_tag
		self.MonitorTags["LastHV02Current"]=self.LastHV02Current_tag
		self.MonitorTags["LastHV03Current"]=self.LastHV03Current_tag
		self.MonitorTags["LastHV04Current"]=self.LastHV04Current_tag
		self.MonitorTags["LastHV05Current"]=self.LastHV05Current_tag
		self.MonitorTags["LastHV06Current"]=self.LastHV06Current_tag
		self.MonitorTags["LastHV07Current"]=self.LastHV07Current_tag
		self.MonitorTags["LastHV08Current"]=self.LastHV08Current_tag
		self.MonitorTags["LastHV09Current"]=self.LastHV09Current_tag
		self.MonitorTags["LastHV00Voltage"]=self.LastHV00Voltage_tag
		self.MonitorTags["LastHV01Voltage"]=self.LastHV01Voltage_tag
		self.MonitorTags["LastHV02Voltage"]=self.LastHV02Voltage_tag
		self.MonitorTags["LastHV03Voltage"]=self.LastHV03Voltage_tag
		self.MonitorTags["LastHV04Voltage"]=self.LastHV04Voltage_tag
		self.MonitorTags["LastHV05Voltage"]=self.LastHV05Voltage_tag
		self.MonitorTags["LastHV06Voltage"]=self.LastHV06Voltage_tag
		self.MonitorTags["LastHV07Voltage"]=self.LastHV07Voltage_tag
		self.MonitorTags["LastHV08Voltage"]=self.LastHV08Voltage_tag
		self.MonitorTags["LastHV09Voltage"]=self.LastHV09Voltage_tag
		self.MonitorTags["LastHV00Status"]=self.LastHV00Status_tag
		self.MonitorTags["LastHV01Status"]=self.LastHV01Status_tag
		self.MonitorTags["LastHV02Status"]=self.LastHV02Status_tag
		self.MonitorTags["LastHV03Status"]=self.LastHV03Status_tag
		self.MonitorTags["LastHV04Status"]=self.LastHV04Status_tag
		self.MonitorTags["LastHV05Status"]=self.LastHV05Status_tag
		self.MonitorTags["LastHV06Status"]=self.LastHV06Status_tag
		self.MonitorTags["LastHV07Status"]=self.LastHV07Status_tag
		self.MonitorTags["LastHV08Status"]=self.LastHV08Status_tag
		self.MonitorTags["LastHV09Status"]=self.LastHV09Status_tag
		self.HV00ID_tag.setText(self.HVNames[0])
		self.HV01ID_tag.setText(self.HVNames[1])
		self.HV02ID_tag.setText(self.HVNames[2])
		self.HV03ID_tag.setText(self.HVNames[3])
		self.HV04ID_tag.setText(self.HVNames[4])
		self.HV05ID_tag.setText(self.HVNames[5])
		self.HV06ID_tag.setText(self.HVNames[6])
		self.HV07ID_tag.setText(self.HVNames[7])
		self.HV08ID_tag.setText(self.HVNames[8])
		self.HV09ID_tag.setText(self.HVNames[9])
		
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
		
		self.MonitorTags["CAEN_table"]=self.Ctrl_CAEN_table

		
		
		# start monitoring function in QThread
		self.MonitorThread = QThread()
		self.Monitor = BurnIn_Monitor(self.configDict,self.logger, self.MonitorTags, self.Julabo, self.FNALBox, self.LVNames, self.HVNames)
		self.Monitor.moveToThread(self.MonitorThread)
		self.MonitorThread.started.connect(self.Monitor.run)
		self.MonitorThread.start()	
		
		
		# start GUI worker in QThread
		self.WorkerThread = QThread()
		self.Worker = BurnIn_Worker(self.configDict,self.logger, self.MonitorTags, self.Julabo, self.FNALBox, self.CAENController)
		self.Worker.moveToThread(self.WorkerThread)
		self.WorkerThread.start()	
		
		#connecting local slots
		
		self.JulaboTestCmd_btn.clicked.connect(self.SendJulaboCmd)	
		self.FNALBoxTestCmd_btn.clicked.connect(self.SendFNALBoxCmd)
		self.CAENControllerTestCmd_btn.clicked.connect(self.SendCAENControllerCmd)
		self.ModuleTestCmd_btn.clicked.connect(self.SendModuleTestCmd)
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
		self.SendCAENControllerCmd_sig.connect(self.Worker.SendCAENControllerCmd)
		self.SendModuleTestCmd_sig.connect(self.Worker.SendModuleTestCmd)
		
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
		
	def SendCAENControllerCmd(self):
		self.SendCAENControllerCmd_sig.emit(self.CAENControllerTestCmd_line.text())
		
	def SendModuleTestCmd(self):
		self.SendModuleTestCmd_sig.emit(self.ModuleTestCmd_line.text())
	
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
		self.statusBar().showMessage("Waiting acknowledge")
		msg.exec()
		self.statusBar().showMessage("System ready")
		
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
