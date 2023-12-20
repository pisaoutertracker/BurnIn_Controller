import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from PyQt5.QtCore import QThread, pyqtSlot, pyqtSignal
import subprocess
import pyqtgraph as pg
import datetime

from BurnIn_TCP import *

from BurnIn_Worker import *
from BurnIn_Monitor import *

import databaseTools
from pprint import pprint
import requests

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
	Ctrl_PowerLV_sig = pyqtSignal(bool)
	Ctrl_PowerHV_sig = pyqtSignal(bool)
	Ctrl_VSet_sig = pyqtSignal(str)
	
	
	MT_UploadDB_sig = pyqtSignal()
	MT_StartTest_sig = pyqtSignal(bool)
	
	BI_Start_sig = pyqtSignal(dict)


	def __init__(self,configDict,logger):
		super(BurnIn_GUI,self).__init__()
		self.is_expert=False
		self.logger=logger
		self.configDict=configDict
	
		self.TestSession="session1" #hardcoded (test value)
		
		self.LVNames=["?"] * 10
		self.LVNames[7]="BLV08"
		self.LVNames[8]="BLV09"
		self.LVNames[9]="BLV10"
	
		self.HVNames=["?"] * 10
		self.HVNames[7]="HV001"
		self.HVNames[8]="HV002"
		self.HVNames[9]="HV003"
		
		self.initUI()
		
		
	def initUI(self):
	
		uic.loadUi('GUI.ui', self) # Load the .ui file
		self.show() # Show the GUI
	
		self.setWindowIcon(QtGui.QIcon('logo.png'))
		self.actionExpert.setIcon(QtGui.QIcon('expert.png'))
		self.actionExit.setIcon(QtGui.QIcon('exit.jpeg')) 
		
		
		self.GraphWidget.setBackground("w")
		styles = { "font-size": "13px"}
		self.GraphWidget.setLabel("left", "Temperature (°C)", **styles)
		self.GraphWidget.setLabel("bottom", "Time (?)", **styles)
		self.GraphWidget.showGrid(x=False, y=True)
		self.GraphWidgetLegend=self.GraphWidget.addLegend(offset=1,colCount=4)
		self.Temp_arr=[]
		self.Time_arr=[]
		self.TempTest_arr=[]
		self.TimeTest_arr=[]
		self.Targ_arr=[]
		self.DewPoint_arr=[]
		pen = pg.mkPen(color='r',width=3)
		self.DewPoint_line=self.GraphWidget.plot(self.Time_arr, self.DewPoint_arr,name="Dew Point", pen=pen)
		pen1 = pg.mkPen(color='g',width=3)
		self.Temp_line=self.GraphWidget.plot(self.Time_arr, self.Temp_arr,name="Temp", pen=pen1)
		pen = pg.mkPen(color='b',width=3)
		self.Targ_line=self.GraphWidget.plot(self.Time_arr, self.Targ_arr,name="Target", pen=pen)  

		self.Test_line=self.GraphWidget.plot(self.TimeTest_arr, self.TempTest_arr, pen=None, symbol='+')		
		
		self.BI_ProgressBar_pb.setValue(0)
		#adjust GUI table elements
		for row in range(10):
			self.Ctrl_CAEN_table.setItem(row,0,QtWidgets.QTableWidgetItem(self.LVNames[row]))
			self.Ctrl_CAEN_table.setItem(row,1,QtWidgets.QTableWidgetItem("?"))
			self.Ctrl_CAEN_table.setItem(row,2,QtWidgets.QTableWidgetItem("?"))
			self.Ctrl_CAEN_table.setItem(row,3,QtWidgets.QTableWidgetItem("?"))
			self.Ctrl_CAEN_table.setItem(row,4,QtWidgets.QTableWidgetItem("?"))
			self.Ctrl_CAEN_table.setItem(row,5,QtWidgets.QTableWidgetItem(self.HVNames[row]))
			self.Ctrl_CAEN_table.setItem(row,6,QtWidgets.QTableWidgetItem("?"))
			self.Ctrl_CAEN_table.setItem(row,7,QtWidgets.QTableWidgetItem("?"))
			self.Ctrl_CAEN_table.setItem(row,8,QtWidgets.QTableWidgetItem("?"))
			self.Ctrl_CAEN_table.setItem(row,9,QtWidgets.QTableWidgetItem("?"))
		
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
		
		
		# pack module IDs button
		self.ModuleId_btns = []
		self.ModuleId_btns.append(self.BI_Mod0ID_btn)
		self.ModuleId_btns.append(self.BI_Mod1ID_btn)
		self.ModuleId_btns.append(self.BI_Mod2ID_btn)
		self.ModuleId_btns.append(self.BI_Mod3ID_btn)
		self.ModuleId_btns.append(self.BI_Mod4ID_btn)
		self.ModuleId_btns.append(self.BI_Mod5ID_btn)
		self.ModuleId_btns.append(self.BI_Mod6ID_btn)
		self.ModuleId_btns.append(self.BI_Mod7ID_btn)
		self.ModuleId_btns.append(self.BI_Mod8ID_btn)
		self.ModuleId_btns.append(self.BI_Mod9ID_btn)
		
		
		self.Module_cbs = []
		self.Module_cbs.append(self.BI_Mod0_cb)
		self.Module_cbs.append(self.BI_Mod1_cb)
		self.Module_cbs.append(self.BI_Mod2_cb)
		self.Module_cbs.append(self.BI_Mod3_cb)
		self.Module_cbs.append(self.BI_Mod4_cb)
		self.Module_cbs.append(self.BI_Mod5_cb)
		self.Module_cbs.append(self.BI_Mod6_cb)
		self.Module_cbs.append(self.BI_Mod7_cb)
		self.Module_cbs.append(self.BI_Mod8_cb)
		self.Module_cbs.append(self.BI_Mod9_cb)
		
		#for cb in self.Module_cbs:
		for i in range (7,10,1):
			self.Module_cbs[i].setChecked(True)
		
		self.JulaboTestCmd_btn.setEnabled(False)    
		self.FNALBoxTestCmd_btn.setEnabled(False)    
		self.CAENControllerTestCmd_btn.setEnabled(False)    
		self.ModuleTestCmd_btn.setEnabled(False)    
		
		
		# creating interfaces
		self.Julabo = BurnIn_TCP(self.configDict,self.logger,"Julabo")
		self.FNALBox = BurnIn_TCP(self.configDict,self.logger,"FNALBox")
		self.CAENController = BurnIn_TCP(self.configDict,self.logger,"CAENController")
	
		
		########## packing shared infrmation ################
		self.SharedDict = {}
	
		# PYQT tags in Monitor tab
		self.SharedDict["LastMonitor"]=self.LastMonitor_tag
		self.SharedDict["MQTTConn"]=self.MQTTConn_tag
		self.SharedDict["JULABOConn"]=self.JULABOConn_tag
		self.SharedDict["FNALConn"]=self.FNALConn_tag
		self.SharedDict["LastMQTTCAENMsgTS"]=self.LastMQTTCAENMsgTS_tag
		self.SharedDict["LastMQTTM5MsgTS"]=self.LastMQTTM5MsgTS_tag
		self.SharedDict["LastM5Temp"]=self.LastM5Temp_tag
		self.SharedDict["LastM5Humi"]=self.LastM5Humi_tag
		self.SharedDict["LastM5Pres"]=self.LastM5Pres_tag
		self.SharedDict["LastM5DP"]=self.LastM5DP_tag
		self.SharedDict["LastJulaboMsgTS"]=self.LastJulaboMsgTS_tag
		self.SharedDict["LastJulaboStatus"]=self.LastJulaboStatus_tag
		self.SharedDict["LastJulaboSP1"]=self.LastJulaboSP1_tag
		self.SharedDict["LastJulaboSP2"]=self.LastJulaboSP2_tag
		self.SharedDict["LastJulaboSP3"]=self.LastJulaboSP3_tag
		self.SharedDict["LastJulaboBT"]=self.LastJulaboBT_tag
		self.SharedDict["LastJulaboHP"]=self.LastJulaboHP_tag
		self.SharedDict["LastJulaboTSP"]=self.LastJulaboTSP_tag
		self.SharedDict["LastFNALBoxMsgTS"]=self.LastFNALBoxMsgTS_tag
		self.SharedDict["LastFNALBoxTemp0"]=self.LastFNALBoxTemp0_tag
		self.SharedDict["LastFNALBoxTemp1"]=self.LastFNALBoxTemp1_tag
		self.SharedDict["LastFNALBoxDP"]=self.LastFNALBoxDP_tag
		self.SharedDict["LastFNALBoxOW0"]=self.LastFNALBoxOW0_tag
		self.SharedDict["LastFNALBoxOW1"]=self.LastFNALBoxOW1_tag
		self.SharedDict["LastFNALBoxOW2"]=self.LastFNALBoxOW2_tag
		self.SharedDict["LastFNALBoxOW3"]=self.LastFNALBoxOW3_tag
		self.SharedDict["LastFNALBoxOW4"]=self.LastFNALBoxOW4_tag
		self.SharedDict["LastFNALBoxOW5"]=self.LastFNALBoxOW5_tag
		self.SharedDict["LastFNALBoxOW6"]=self.LastFNALBoxOW6_tag
		self.SharedDict["LastFNALBoxOW7"]=self.LastFNALBoxOW7_tag
		self.SharedDict["LastFNALBoxOW8"]=self.LastFNALBoxOW8_tag
		self.SharedDict["LastFNALBoxOW9"]=self.LastFNALBoxOW9_tag
		self.SharedDict["LastFNALBoxDoor"]=self.LastFNALBoxDoor_tag
		
		
		self.SharedDict["LastLV00Current"]=self.LastLV00Current_tag
		self.SharedDict["LastLV01Current"]=self.LastLV01Current_tag
		self.SharedDict["LastLV02Current"]=self.LastLV02Current_tag
		self.SharedDict["LastLV03Current"]=self.LastLV03Current_tag
		self.SharedDict["LastLV04Current"]=self.LastLV04Current_tag
		self.SharedDict["LastLV05Current"]=self.LastLV05Current_tag
		self.SharedDict["LastLV06Current"]=self.LastLV06Current_tag
		self.SharedDict["LastLV07Current"]=self.LastLV07Current_tag
		self.SharedDict["LastLV08Current"]=self.LastLV08Current_tag
		self.SharedDict["LastLV09Current"]=self.LastLV09Current_tag
		self.SharedDict["LastLV00Voltage"]=self.LastLV00Voltage_tag
		self.SharedDict["LastLV01Voltage"]=self.LastLV01Voltage_tag
		self.SharedDict["LastLV02Voltage"]=self.LastLV02Voltage_tag
		self.SharedDict["LastLV03Voltage"]=self.LastLV03Voltage_tag
		self.SharedDict["LastLV04Voltage"]=self.LastLV04Voltage_tag
		self.SharedDict["LastLV05Voltage"]=self.LastLV05Voltage_tag
		self.SharedDict["LastLV06Voltage"]=self.LastLV06Voltage_tag
		self.SharedDict["LastLV07Voltage"]=self.LastLV07Voltage_tag
		self.SharedDict["LastLV08Voltage"]=self.LastLV08Voltage_tag
		self.SharedDict["LastLV09Voltage"]=self.LastLV09Voltage_tag
		self.SharedDict["LastLV00VoltageSet"]=self.LastLV00VoltageSet_tag
		self.SharedDict["LastLV01VoltageSet"]=self.LastLV01VoltageSet_tag
		self.SharedDict["LastLV02VoltageSet"]=self.LastLV02VoltageSet_tag
		self.SharedDict["LastLV03VoltageSet"]=self.LastLV03VoltageSet_tag
		self.SharedDict["LastLV04VoltageSet"]=self.LastLV04VoltageSet_tag
		self.SharedDict["LastLV05VoltageSet"]=self.LastLV05VoltageSet_tag
		self.SharedDict["LastLV06VoltageSet"]=self.LastLV06VoltageSet_tag
		self.SharedDict["LastLV07VoltageSet"]=self.LastLV07VoltageSet_tag
		self.SharedDict["LastLV08VoltageSet"]=self.LastLV08VoltageSet_tag
		self.SharedDict["LastLV09VoltageSet"]=self.LastLV09VoltageSet_tag
		self.SharedDict["LastLV00Status"]=self.LastLV00Status_tag
		self.SharedDict["LastLV01Status"]=self.LastLV01Status_tag
		self.SharedDict["LastLV02Status"]=self.LastLV02Status_tag
		self.SharedDict["LastLV03Status"]=self.LastLV03Status_tag
		self.SharedDict["LastLV04Status"]=self.LastLV04Status_tag
		self.SharedDict["LastLV05Status"]=self.LastLV05Status_tag
		self.SharedDict["LastLV06Status"]=self.LastLV06Status_tag
		self.SharedDict["LastLV07Status"]=self.LastLV07Status_tag
		self.SharedDict["LastLV08Status"]=self.LastLV08Status_tag
		self.SharedDict["LastLV09Status"]=self.LastLV09Status_tag
		
		self.SharedDict["LastHV00Current"]=self.LastHV00Current_tag
		self.SharedDict["LastHV01Current"]=self.LastHV01Current_tag
		self.SharedDict["LastHV02Current"]=self.LastHV02Current_tag
		self.SharedDict["LastHV03Current"]=self.LastHV03Current_tag
		self.SharedDict["LastHV04Current"]=self.LastHV04Current_tag
		self.SharedDict["LastHV05Current"]=self.LastHV05Current_tag
		self.SharedDict["LastHV06Current"]=self.LastHV06Current_tag
		self.SharedDict["LastHV07Current"]=self.LastHV07Current_tag
		self.SharedDict["LastHV08Current"]=self.LastHV08Current_tag
		self.SharedDict["LastHV09Current"]=self.LastHV09Current_tag
		self.SharedDict["LastHV00Voltage"]=self.LastHV00Voltage_tag
		self.SharedDict["LastHV01Voltage"]=self.LastHV01Voltage_tag
		self.SharedDict["LastHV02Voltage"]=self.LastHV02Voltage_tag
		self.SharedDict["LastHV03Voltage"]=self.LastHV03Voltage_tag
		self.SharedDict["LastHV04Voltage"]=self.LastHV04Voltage_tag
		self.SharedDict["LastHV05Voltage"]=self.LastHV05Voltage_tag
		self.SharedDict["LastHV06Voltage"]=self.LastHV06Voltage_tag
		self.SharedDict["LastHV07Voltage"]=self.LastHV07Voltage_tag
		self.SharedDict["LastHV08Voltage"]=self.LastHV08Voltage_tag
		self.SharedDict["LastHV09Voltage"]=self.LastHV09Voltage_tag
		self.SharedDict["LastHV00VoltageSet"]=self.LastHV00VoltageSet_tag
		self.SharedDict["LastHV01VoltageSet"]=self.LastHV01VoltageSet_tag
		self.SharedDict["LastHV02VoltageSet"]=self.LastHV02VoltageSet_tag
		self.SharedDict["LastHV03VoltageSet"]=self.LastHV03VoltageSet_tag
		self.SharedDict["LastHV04VoltageSet"]=self.LastHV04VoltageSet_tag
		self.SharedDict["LastHV05VoltageSet"]=self.LastHV05VoltageSet_tag
		self.SharedDict["LastHV06VoltageSet"]=self.LastHV06VoltageSet_tag
		self.SharedDict["LastHV07VoltageSet"]=self.LastHV07VoltageSet_tag
		self.SharedDict["LastHV08VoltageSet"]=self.LastHV08VoltageSet_tag
		self.SharedDict["LastHV09VoltageSet"]=self.LastHV09VoltageSet_tag
		self.SharedDict["LastHV00Status"]=self.LastHV00Status_tag
		self.SharedDict["LastHV01Status"]=self.LastHV01Status_tag
		self.SharedDict["LastHV02Status"]=self.LastHV02Status_tag
		self.SharedDict["LastHV03Status"]=self.LastHV03Status_tag
		self.SharedDict["LastHV04Status"]=self.LastHV04Status_tag
		self.SharedDict["LastHV05Status"]=self.LastHV05Status_tag
		self.SharedDict["LastHV06Status"]=self.LastHV06Status_tag
		self.SharedDict["LastHV07Status"]=self.LastHV07Status_tag
		self.SharedDict["LastHV08Status"]=self.LastHV08Status_tag
		self.SharedDict["LastHV09Status"]=self.LastHV09Status_tag
		
		
		# PYQT tags in Control tab
		
		self.SharedDict["Ctrl_Sp1"]=self.Ctrl_Sp1_tag
		self.SharedDict["Ctrl_Sp2"]=self.Ctrl_Sp2_tag
		self.SharedDict["Ctrl_Sp3"]=self.Ctrl_Sp3_tag
		self.SharedDict["Ctrl_TSp"]=self.Ctrl_TSp_tag
		self.SharedDict["Ctrl_StatusJulabo"]=self.Ctrl_StatusJulabo_tag
		self.SharedDict["Ctrl_TargetTemp"]=self.Ctrl_TargetTemp_tag
		self.SharedDict["Ctrl_IntDewPoint"]=self.Ctrl_IntDewPoint_tag
		self.SharedDict["Ctrl_ExtDewPoint"]=self.Ctrl_ExtDewPoint_tag
		
		self.SharedDict["Ctrl_StatusFlow"]=self.Ctrl_StatusFlow_tag
		self.SharedDict["Ctrl_StatusLock"]=self.Ctrl_StatusLock_tag
		self.SharedDict["Ctrl_StatusDoor"]=self.Ctrl_StatusDoor_tag
		self.SharedDict["Ctrl_LowerTemp"]=999.0
		
		
		# PYQT tags in BI tab
		
		self.SharedDict["BI_Status"]=self.BI_Status_tag
		self.SharedDict["BI_Action"]=self.BI_Action_tag
		self.SharedDict["BI_ProgressBar"]=self.BI_ProgressBar_pb
		self.SharedDict["BI_Cycle"]=self.BI_Cycle_tag
		
		# Status variable & parameter
		
		self.SharedDict["M5_updated"]=False
		self.SharedDict["Julabo_updated"]=False
		self.SharedDict["FNALBox_updated"]=False
		self.SharedDict["CAEN_updated"]=False
		self.SharedDict["WaitInput"]=False
		self.SharedDict["BI_Active"]=False
		self.SharedDict["BI_TestActive"]=False
		self.SharedDict["BI_StopRequest"]=False
		
		self.SharedDict["Input"]=0.0
		self.SharedDict["TestSession"]="0"
		
		self.SharedDict["CAEN_table"]=self.Ctrl_CAEN_table
		self.SharedDict["BI_Graph"]=self.GraphWidget
		self.SharedDict["DewPoint_arr"]=self.DewPoint_arr
		self.SharedDict["Temp_arr"]=self.Temp_arr
		self.SharedDict["Time_arr"]=self.Time_arr
		self.SharedDict["Targ_arr"]=self.Targ_arr
		self.SharedDict["TimeTest_arr"]=self.TimeTest_arr
		self.SharedDict["TempTest_arr"]=self.TempTest_arr
		
		# start monitoring function in QThread
		self.MonitorThread = QThread()
		self.Monitor = BurnIn_Monitor(self.configDict,self.logger, self.SharedDict, self.Julabo, self.FNALBox, self.LVNames, self.HVNames)
		self.Monitor.moveToThread(self.MonitorThread)
		self.MonitorThread.started.connect(self.Monitor.run)
		self.MonitorThread.start()    
		
		
		# start GUI worker in QThread
		self.WorkerThread = QThread()
		self.Worker = BurnIn_Worker(self.configDict,self.logger, self.SharedDict, self.Julabo, self.FNALBox, self.CAENController)
		self.Worker.moveToThread(self.WorkerThread)
		self.WorkerThread.start()    
		###########################################
		#connecting local signals to local slots
		###########################################
		
		#free test tab
		self.JulaboTestCmd_btn.clicked.connect(self.SendJulaboCmd)    
		self.FNALBoxTestCmd_btn.clicked.connect(self.SendFNALBoxCmd)
		self.CAENControllerTestCmd_btn.clicked.connect(self.SendCAENControllerCmd)
		self.ModuleTestCmd_btn.clicked.connect(self.SendModuleTestCmd)
	
		# module test tab
		#self.Ctrl_StartSesh_btn.clicked.connect(self.MT_UploadDB_Cmd)
		self.Ctrl_StartSesh_btn.clicked.connect(self.Ctrl_StartSesh_Cmd)
		self.Ctrl_StartTest_btn.clicked.connect(self.MT_StartTest_Cmd)
		
		# manual operation tab
		self.Ctrl_SetSp1_btn.clicked.connect(lambda : self.Ctrl_SetSp_Cmd(0,self.Ctrl_ValSp1_dsb.value()))
		self.Ctrl_SetSp2_btn.clicked.connect(lambda : self.Ctrl_SetSp_Cmd(1,self.Ctrl_ValSp2_dsb.value()))
		self.Ctrl_SetSp3_btn.clicked.connect(lambda : self.Ctrl_SetSp_Cmd(2,self.Ctrl_ValSp3_dsb.value()))
		self.Ctrl_SelSp1_btn.clicked.connect(lambda : self.Ctrl_SelSp_Cmd(0))
		self.Ctrl_SelSp2_btn.clicked.connect(lambda : self.Ctrl_SelSp_Cmd(1))
		self.Ctrl_SelSp3_btn.clicked.connect(lambda : self.Ctrl_SelSp_Cmd(2))
		self.ModuleId_btns[0].clicked.connect(lambda : self.BI_SetModuleID(0))
		self.ModuleId_btns[1].clicked.connect(lambda : self.BI_SetModuleID(1))
		self.ModuleId_btns[2].clicked.connect(lambda : self.BI_SetModuleID(2))
		self.ModuleId_btns[3].clicked.connect(lambda : self.BI_SetModuleID(3))
		self.ModuleId_btns[4].clicked.connect(lambda : self.BI_SetModuleID(4))
		self.ModuleId_btns[5].clicked.connect(lambda : self.BI_SetModuleID(5))
		self.ModuleId_btns[6].clicked.connect(lambda : self.BI_SetModuleID(6))
		self.ModuleId_btns[7].clicked.connect(lambda : self.BI_SetModuleID(7))
		self.ModuleId_btns[8].clicked.connect(lambda : self.BI_SetModuleID(8))
		self.ModuleId_btns[9].clicked.connect(lambda : self.BI_SetModuleID(9))
		self.Ctrl_SetLowFlow_btn.clicked.connect(lambda : self.Ctrl_SetHighFlow_Cmd(False))
		self.Ctrl_SetHighFlow_btn.clicked.connect(lambda : self.Ctrl_SetHighFlow_Cmd(True))
		self.Ctrl_SetLock_btn.clicked.connect    (lambda : self.Ctrl_SetLock_Cmd(True))
		self.Ctrl_SetUnlock_btn.clicked.connect  (lambda : self.Ctrl_SetLock_Cmd(False))
		self.Ctrl_StartJulabo_btn.clicked.connect(lambda : self.Ctrl_PowerJulabo_Cmd(True))
		self.Ctrl_StopJulabo_btn.clicked.connect (lambda : self.Ctrl_PowerJulabo_Cmd(False))
		self.Ctrl_LVOn_btn.clicked.connect(lambda : self.Ctrl_PowerLV_Cmd(True))
		self.Ctrl_LVOff_btn.clicked.connect (lambda : self.Ctrl_PowerLV_Cmd(False))
		self.Ctrl_HVOn_btn.clicked.connect(lambda : self.Ctrl_PowerHV_Cmd(True))
		self.Ctrl_HVOff_btn.clicked.connect (lambda : self.Ctrl_PowerHV_Cmd(False))
		self.Ctrl_LVSet_btn.clicked.connect(lambda : self.Ctrl_VSet_Cmd("LV"))
		self.Ctrl_HVSet_btn.clicked.connect(lambda : self.Ctrl_VSet_Cmd("HV"))
		
		#BI tab
		self.BI_Stop_btn.clicked.connect(self.BI_Stop_Cmd)
		self.BI_Start_btn.clicked.connect(self.BI_Start_Cmd)
		
		#menu actions
		self.actionExit.triggered.connect(self.close)
		self.actionExpert.triggered.connect(self.expert)
		
		##############################################
		#connecting local signals to worker slots
		#############################################
		self.SendJulaboCmd_sig.connect(self.Worker.SendJulaboCmd)
		self.SendFNALBoxCmd_sig.connect(self.Worker.SendFNALBoxCmd)
		self.SendCAENControllerCmd_sig.connect(self.Worker.SendCAENControllerCmd)
		self.SendModuleTestCmd_sig.connect(self.Worker.SendModuleTestCmd)
		
		self.Ctrl_SelSp_sig.connect(self.Worker.Ctrl_SelSp_Cmd)
		self.Ctrl_SetSp_sig.connect(self.Worker.Ctrl_SetSp_Cmd)
		self.Ctrl_PowerJulabo_sig.connect(self.Worker.Ctrl_PowerJulabo_Cmd)
		self.Ctrl_SetLock_sig.connect(self.Worker.Ctrl_SetLock_Cmd)
		self.Ctrl_SetHighFlow_sig.connect(self.Worker.Ctrl_SetHighFlow_Cmd)
		self.Ctrl_PowerLV_sig.connect(self.Worker.Ctrl_PowerLV_Cmd)
		self.Ctrl_PowerHV_sig.connect(self.Worker.Ctrl_PowerHV_Cmd)
		self.Ctrl_VSet_sig.connect(self.Worker.Ctrl_VSet_Cmd)
		
		self.MT_UploadDB_sig.connect(self.Worker.MT_UploadDB_Cmd)
		self.MT_StartTest_sig.connect(self.Worker.MT_StartTest_Cmd)
		
		
		self.BI_Start_sig.connect(self.Worker.BI_Start_Cmd)
		
		#################################################
		#connecting worker/monitor signals to local slots
		##################################################
		self.Worker.Request_msg.connect(self.Show_msg)
		self.Worker.Request_input_dsb.connect(self.Show_input_dsb)
		self.Worker.BI_terminated.connect(self.BI_terminated)
		self.Monitor.Update_graph.connect(self.Update_graph)
		#self.Monitor.Update_manualOp_tab.connect(self.Update_manualOp_tab)
		
		self.Worker.UploadDB_sig.connect(self.Ctrl_StartSesh_Cmd)
		
		
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
	
	def Ctrl_PowerLV_Cmd(self,switch):
		self.Ctrl_PowerLV_sig.emit(switch)
	
	def Ctrl_PowerHV_Cmd(self,switch):
		self.Ctrl_PowerHV_sig.emit(switch)
	
	def Ctrl_SetHighFlow_Cmd(self,switch):
		self.Ctrl_SetHighFlow_sig.emit(switch)
	
	def Ctrl_SetLock_Cmd(self,switch):
		self.Ctrl_SetLock_sig.emit(switch)
	
	def Ctrl_VSet_Cmd(self,VType):
		self.Ctrl_VSet_sig.emit(VType)
	
	def MT_StartTest_Cmd(self):
		self.MT_StartTest_sig.emit(self.Ctrl_DryRun_cb.isChecked())
	
	def MT_UploadDB_Cmd(self):
		self.MT_UploadDB_sig.emit()
	
	def BI_Start_Cmd(self):
		self.Temp_arr.clear()
		self.Time_arr.clear()
		self.Targ_arr.clear()
		self.TimeTest_arr.clear()
		self.TempTest_arr.clear()
		self.DewPoint_arr.clear()
		self.SeshDescription_db.setText(self.BI_Desc_line.text())
		self.ManualOp_tab.setEnabled(False)
		self.ModuleTest_tab.setEnabled(False)
		BI_Options={}
		BI_Options["LowTemp"]= self.BI_LowTemp_dsb.value()
		BI_Options["HighTemp"]= self.BI_HighTemp_dsb.value()
		BI_Options["UnderRamp"]=self.BI_UnderRampTemp_dsb.value()
		BI_Options["UnderKeep"]=self.BI_UnderKeepTemp_dsb.value()
		BI_Options["NCycles"]=self.BI_NCycles_sb.value()
		BI_Options["Operator"]=self.BI_Operator_line.text()
		BI_Options["ActiveSlots"]=[]
		for cb in self.Module_cbs:
			BI_Options["ActiveSlots"].append(cb.isChecked)
		self.BI_Start_sig.emit(BI_Options)
	
	
	def BI_Stop_Cmd(self):
		self.logger.info("Requesting BurnIn stop...")
		if self.SharedDict["BI_Active"]:
			self.SharedDict["BI_StopRequest"]=True
			self.logger.info("BURN IN stop request issued")
		else:
			self.logger.info("NO Burn In test ongoing. Request cancelled")
	
	@pyqtSlot()
	def BI_terminated(self):
		self.ManualOp_tab.setEnabled(True) 
		self.ModuleTest_tab.setEnabled(True)
		
	def BI_SetModuleID(self,idx):
		
		Id, ok = QtWidgets.QInputDialog.getText(self,"Enter or scan module IDs","Module ID") 
		if ok:
			self.ModuleId_btns[idx].setText(Id)
			self.logger.info("New Id for module "+str(idx)+": "+Id)
		else:
			self.logger.info("New Id for module "+str(idx)+" aborted by user")
		
	@pyqtSlot()					
	def Ctrl_StartSesh_Cmd(self):
		self.logger.info("Starting Test Session")
		msg = QMessageBox()
		msg.setWindowTitle("Database session starting. Please wait...")
		msg.show()
                
		#define test session for DB
		session = {
			"operator": self.BI_Operator_line.text(),
			"timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                	"description": self.SeshDescription_db.text(), 
			"temperatures": {
				"low": self.BI_LowTemp_dsb.value(),
        			"high": self.BI_HighTemp_dsb.value(),
                	},                        
#			"configuration": [""]*10,
			"modulesList": [],
                }

                #omit disabled modules
		for i in range(10):
			if self.Module_cbs[i].isChecked()==False:
#				session["configuration"][i]=""
                                session["modulesList"].append("")
			else:
				session["modulesList"].append(self.ModuleId_btns[i].text()),
        
                #send session to MongoDB here
		uploadResponse=databaseTools.uploadSessionToDB(session)
                #(make sure the Session ID doesn't already exist)
                #now get it back to display
		if uploadResponse=="timeout": #if it times out, display a dummy status
			session_fromDB=session
			self.TestSession=uploadResponse
			self.SharedDict["TestSession"]=self.TestSession
			self.logger.info("Session timed out!")
		else:
			session_fromDB=databaseTools.getSessionFromDB(sessionName=uploadResponse)#default for testing
			self.TestSession=session_fromDB["sessionName"]
			self.SharedDict["TestSession"]=self.TestSession
			self.logger.info("Session started!")
			pprint(session_fromDB)
		#
		self.Ctrl_SeshID_db.setText("Session ID: "+str(self.TestSession))
		self.Ctrl_Operator_db.setText("Operator: "+session_fromDB["operator"])
		self.Ctrl_StartTime_db.setText("Start Time: "+session_fromDB["timestamp"])
		self.Ctrl_SeshDescription_db.setText("Session Description: "+session_fromDB["description"])
		self.Ctrl_lowTemp_db.setText("Low Temp (C°): "+str(session_fromDB["temperatures"]["low"]))
		self.Ctrl_hiTemp_db.setText("High Temp (C°): "+str(session_fromDB["temperatures"]["high"]))
		self.Ctrl_Module00_tag.setText("Module 00: "+str(session_fromDB["modulesList"][0]))
		self.Ctrl_Module01_tag.setText("Module 01: "+str(session_fromDB["modulesList"][1]))
		self.Ctrl_Module02_tag.setText("Module 02: "+str(session_fromDB["modulesList"][2]))
		self.Ctrl_Module03_tag.setText("Module 03: "+str(session_fromDB["modulesList"][3]))
		self.Ctrl_Module04_tag.setText("Module 04: "+str(session_fromDB["modulesList"][4]))
		self.Ctrl_Module05_tag.setText("Module 05: "+str(session_fromDB["modulesList"][5]))
		self.Ctrl_Module06_tag.setText("Module 06: "+str(session_fromDB["modulesList"][6]))
		self.Ctrl_Module07_tag.setText("Module 07: "+str(session_fromDB["modulesList"][7]))
		self.Ctrl_Module08_tag.setText("Module 08: "+str(session_fromDB["modulesList"][8]))
		self.Ctrl_Module09_tag.setText("Module 09: "+str(session_fromDB["modulesList"][9]))
		
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
		
	@pyqtSlot(str,float,float,float)
	def Show_input_dsb(self,msg, startVal, minVal, maxVal):
	
		value, ok = QtWidgets.QInputDialog.getDouble(self,msg,"New value", startVal,minVal, maxVal, 1) 
		if ok:
			self.SharedDict["Input"]=value
			self.SharedDict["WaitInput"]=False
		else:
			self.SharedDict["Input"]=-1
			self.SharedDict["WaitInput"]=False
			
		
	def expert(self):
		psw, ok = QtWidgets.QInputDialog.getText(None, "Expert mode", "Password?", QtWidgets.QLineEdit.Password)
		if psw=='1234' and ok:
			self.logger.info("Expert mode activated")
			self.statusBar().showMessage("Expert mode activated")
			self.is_expert=True
			self.JulaboTestCmd_btn.setEnabled(True)    
			self.FNALBoxTestCmd_btn.setEnabled(True)    
			self.CAENControllerTestCmd_btn.setEnabled(True)    
			self.ModuleTestCmd_btn.setEnabled(True)
			
	@pyqtSlot()
	def Update_graph(self):
		self.DewPoint_line.setData(self.Time_arr,self.DewPoint_arr)
		self.Temp_line.setData(self.Time_arr,self.Temp_arr)
		self.Targ_line.setData(self.Time_arr,self.Targ_arr)
		self.Test_line.setData(self.TimeTest_arr,self.TempTest_arr)
	
		#@pyqtSlot()
		#def Update_manualOp_tab(self):
		#	self.ManualOp_tab.update()
		#	self.Ctrl_CAEN_table.update()
		#	self.Ctrl_CAEN_table.repaint()
		

if __name__== '__main__':
    
    app = QtWidgets.QApplication(sys.argv)
    BurnIn_app = BurnIn_GUI(0, 0)
    sys.exit(app.exec_()) #continua esecuzione finchè non chiudo
