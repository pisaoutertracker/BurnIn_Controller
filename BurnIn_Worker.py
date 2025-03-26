import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
import time
from datetime import datetime
import subprocess
from __Constant import *
import json




## Class implementation for the Worker module of the GUI controller.
#
#  The worker is a inheriting from pyQt library in order to create assign slots and signals
class BurnIn_Worker(QObject):

    Request_msg = pyqtSignal(str,str)
    Request_confirm_sig = pyqtSignal(str)
    Request_input_dsb = pyqtSignal(str,float,float,float)
    BI_terminated = pyqtSignal()
    
    BI_Update_GUI_sig = pyqtSignal(dict)
    BI_CheckID_isOK_sig = pyqtSignal(int,int)
    BI_Clear_Monitor_sig = pyqtSignal()
    BI_Update_PowerStatus_sig = pyqtSignal(int,bool,str)

    ## Init function.
    def __init__(self,configDict,logger, SharedDict, Julabo, FNALBox, CAENController, DB_interface):

    
        super(BurnIn_Worker,self).__init__();
        self.configDict=configDict
        self.logger = logger
        self.Julabo = Julabo
        self.FNALBox = FNALBox
        self.DB_interface = DB_interface
        self.CAENController = CAENController
        self.SharedDict = SharedDict
        
        self.BIcwd = configDict.get(("BITest","cwd"),"NOKEY")
        if self.BIcwd == "NOKEY":
            self.BIcwd = "/home/thermal/BurnIn_moduleTest"
            self.logger.warning("cwd directory parameter not found. Using default")
            
        self.Ph2_ACF_version = configDict.get(("BITest","version"),"NOKEY")
        if self.Ph2_ACF_version == "NOKEY":
            self.Ph2_ACF_version = "latest"
            self.logger.warning("Ph2_ACF_version parameter not found. Using latest")
            
        self.IV_scanType = configDict.get(("IVScan","scanType"),"NOKEY")
        if self.IV_scanType == "NOKEY":
            self.IV_scanType = "before_encapsulation"
            self.logger.warning("IV_scanType parameter not found. Using before_encapsulation")
            
        self.IV_delay = configDict.get(("IVScan","delay"),"NOKEY")
        if self.IV_delay == "NOKEY":
            self.IV_delay = "5.0"
            self.logger.warning("IV_delay parameter not found. Using 5.0")
            
        self.IV_settlingTime = configDict.get(("IVScan","settlingTime"),"NOKEY")
        if self.IV_settlingTime == "NOKEY":
            self.IV_settlingTime = "0.5"
            self.logger.warning("IV_settlingTime parameter not found. Using 0.5")
            
        
        self.logger.info("Worker class initialized")
        self.last_op_ok= True
        
        
    #################################################################
    ## Basic functions. directly called from "Test Operation tab"
    #################################################################
    
    ## Function to send a cmd string to the Julabo interface
    # implemented as a is a Pyqt slot
    # NOT executed if:
    # - TCP socket is not connected and connection attempt fails
    # Control on cmd execution: none
    @pyqtSlot(str)
    def SendJulaboCmd(self,cmd):
        self.Julabo.lock.acquire()
        self.logger.info("Sending Julabo cmd "+cmd)
        if not self.Julabo.is_connected :
            self.Julabo.connect()
        if self.Julabo.is_connected :
            self.Julabo.sendTCP(cmd)
            self.logger.info(self.Julabo.receive())
        else:    
            self.last_op_ok= False    
        self.Julabo.lock.release()
        
    ## Function to send a cmd string to the CAEN controller interface
    # implemented as a is a Pyqt slot
    # NOT executed if:
    # - TCP socket is not connected and connection attempt fails    
    # Control on cmd execution: none
    @pyqtSlot(str)
    def SendCAENControllerCmd(self,cmd):
        self.CAENController.lock.acquire()
        self.logger.info("Sending CAENController cmd "+cmd)
        if not self.CAENController.is_connected :
            self.CAENController.connect()
        if self.CAENController.is_connected :
            self.CAENController.sendTCP(cmd)
            time.sleep(CAEN_SLEEP_AFTER_TCP)
            self.logger.info(self.CAENController.receive())
            self.CAENController.close()
        else:    
            self.last_op_ok= False    
        self.CAENController.lock.release()
    

    ## Function to send a cmd string to the Julabo interface
    # implemented as a is a Pyqt slot
    # NOT executed if:
    # - TCP socket is not connected and connection attempt fails    
    # Control on cmd execution: none
    @pyqtSlot(str)
    def SendFNALBoxCmd(self,cmd):
        self.logger.info("WORKER: Requesting lock on FNALBox")
        self.FNALBox.lock.acquire()
        self.logger.info("Sending FNALBox cmd "+cmd)
        if not self.FNALBox.is_connected :
            self.FNALBox.connect()
        if self.FNALBox.is_connected :
            self.FNALBox.sendTCP(cmd)
            time.sleep(FNAL_SLEEP_AFTER_TCP)
            self.logger.info(self.FNALBox.receive())
        else:    
            self.last_op_ok= False    
        self.FNALBox.lock.release()
        self.logger.info("WORKER: lock on FNALBox released")
        
    ## Function to start a test
    # implemented as a is a Pyqt slot
    @pyqtSlot(str)
    def SendModuleTestCmd(self,cmd):
        self.logger.info("Starting custom shell command...")
        cmdSplit = cmd.split()
        
        try:
            proc = subprocess.Popen(cmdSplit, cwd=self.BIcwd,stdout=subprocess.PIPE, stderr=subprocess.STDOUT)                        
                    
            while(proc.returncode==None):
            
                try:
                    outs, errs = proc.communicate(timeout=TEST_PROCESS_SLEEP)
                    self.logger.info("Custom command output: "+outs.decode())
                    #self.logger.error("BI TEST SUBPROCESS: "+errs.decode())
                    break
                except subprocess.TimeoutExpired:
                    self.logger.info("WORKER: Waiting command completion....")
                    
                if proc.returncode ==0:
                    self.logger.info("Command executed with return code "+str(proc.returncode))
                elif proc.returncode==None:
                    self.logger.info("Command executed with return code NONE")
                else:
                    self.logger.error("Command failed with return code "+str(proc.returncode))
                        
        except Exception as e:
            self.logger.error("Erro while executing custom command")
            self.logger.error(e)
                            
        
        
    ###########################################################################
    ## Safe operation functions. Directly called from "Manual Operation tab"
    ###########################################################################
    
    ## Function to select the SetPoint of the Julabo
    # implemented as a is a Pyqt slot
    # NOT Executed if:
    # - JULABO and FNAL info are not updated    
    # - JULABO is ON and the selected setpoint has a target temperature below the DewPoint
    # - TCP socket is not connected and connection attempt fails    
    # Control on cmd execution: read back from instrument
    @pyqtSlot(int)    
    def Ctrl_SelSp_Cmd(self,Sp_id, PopUp=True):
        self.last_op_ok= True
        self.logger.info("WORKER: Selecting JULABO Sp"+str(Sp_id+1))
        if not (self.SharedDict["Julabo_updated"] and self.SharedDict["FNALBox_updated"]):
            Warning_str = "Operation can't be performed"
            Reason_str = "Julabo and/or FNAL box info are not updated"
            if PopUp:
                self.Request_msg.emit(Warning_str,Reason_str)
            self.last_op_ok= False
            return
            
        if (self.SharedDict["Ctrl_StatusJulabo"].text().find("START") != -1):
            targetT = -100.0
            if Sp_id == 0 :
                targetT = float(self.SharedDict["Ctrl_Sp1"].text())
            elif Sp_id == 1 :
                targetT = float(self.SharedDict["Ctrl_Sp2"].text())
            elif Sp_id == 2 :
                targetT = float(self.SharedDict["Ctrl_Sp3"].text())

            if targetT  < float(self.SharedDict["Ctrl_IntDewPoint"].text()):
                Warning_str = "Operation can't be performed"
                Reason_str = "Set point is configured with a temperature below internal dew point"
                if PopUp:
                    self.Request_msg.emit(Warning_str,Reason_str)
                self.last_op_ok= False
                return
        self.Julabo.lock.acquire()
        self.logger.debug("WORKER: Sending Julabo cmd" )
        if not self.Julabo.is_connected :
            self.Julabo.connect()
        if self.Julabo.is_connected :
            try:
                self.Julabo.sendTCP("out_mode_01 "+str(Sp_id))
                self.logger.info("WORKER: JULABO cmd sent")
                self.Julabo.sendTCP("in_mode_01")
                reply = self.Julabo.receive()
                if (reply != "None" and reply != "TCP error"):
                    Sp = str(int(reply.replace(" ", ""))+1)
                    self.SharedDict["Ctrl_TSp"].setText(Sp)
                if self.SharedDict["Ctrl_TSp"].text()[:1]=="1":
                    self.SharedDict["Ctrl_TargetTemp"].setText(self.SharedDict["Ctrl_Sp1"].text())
                elif self.SharedDict["Ctrl_TSp"].text()[:1]=="2":
                    self.SharedDict["Ctrl_TargetTemp"].setText(self.SharedDict["Ctrl_Sp2"].text())
                elif self.SharedDict["Ctrl_TSp"].text()[:1]=="3":
                    self.SharedDict["Ctrl_TargetTemp"].setText(self.SharedDict["Ctrl_Sp3"].text())
            except Exception as e:
                self.logger.error(e)
                self.last_op_ok= False
        else:
                Warning_str = "Operation can't be performed"
                Reason_str = "Can't connect to JULABO"
                if PopUp:
                    self.Request_msg.emit(Warning_str,Reason_str)
                self.last_op_ok= False
        
        self.Julabo.lock.release()
            
    ## Function to select the target temperature of a JULABO SetPoint
    # implemented as a is a Pyqt slot
    # NOT Executed if:
    # - JULABO and FNAL info are not updated    
    # - JULABO is ON and the selected setpoint has a target temperature below the DewPoint
    # - TCP socket is not connected and connection attempt fails    
    # Control on cmd execution: read back from instrument    
    @pyqtSlot(int,float)    
    def Ctrl_SetSp_Cmd(self,Sp_id,value, PopUp=True):
        self.last_op_ok= True
        self.logger.info("WORKER: Setting JULABO Sp"+str(Sp_id+1)+ " to " +str(value))
        if not (self.SharedDict["Julabo_updated"] and self.SharedDict["FNALBox_updated"]):
            Warning_str = "Operation can't be performed"
            Reason_str = "Julabo and/or FNAL box info are not updated"
            if PopUp:
                self.Request_msg.emit(Warning_str,Reason_str)
            self.last_op_ok= False
            return    
        if (self.SharedDict["Ctrl_StatusJulabo"].text().find("START") != -1):
            Sp_actual = int(self.SharedDict["Ctrl_TSp"].text())-1
            if Sp_actual==Sp_id and  value  < float(self.SharedDict["Ctrl_IntDewPoint"].text()):
                Warning_str = "Operation can't be performed"
                Reason_str = "Attempting to set target temperature of the active set point below internal dew point"
                self.logger.warning(Warning_str)
                self.logger.warning(Reason_str)
                if PopUp:
                    self.Request_msg.emit(Warning_str,Reason_str)
                self.last_op_ok= False
                return
        self.Julabo.lock.acquire()
        self.logger.debug("WORKER: Sending Julabo cmd" )
        if not self.Julabo.is_connected :
            self.Julabo.connect()
        if self.Julabo.is_connected :
            try:
                self.Julabo.sendTCP("out_sp_0"+str(Sp_id)+" "+str(value))
                self.logger.info("WORKER: JULABO cmd sent")                    
                self.Julabo.sendTCP("in_sp_0"+str(Sp_id))
                reply = self.Julabo.receive()
                if (reply != "None" and reply != "TCP error"):
                    self.SharedDict["Ctrl_Sp"+str(Sp_id+1)].setText(reply.replace(" ", ""))
                if self.SharedDict["Ctrl_TSp"].text()[:1]=="1":
                    self.SharedDict["Ctrl_TargetTemp"].setText(self.SharedDict["Ctrl_Sp1"].text())
                elif self.SharedDict["Ctrl_TSp"].text()[:1]=="2":
                    self.SharedDict["Ctrl_TargetTemp"].setText(self.SharedDict["Ctrl_Sp2"].text())
                elif self.SharedDict["Ctrl_TSp"].text()[:1]=="3":
                    self.SharedDict["Ctrl_TargetTemp"].setText(self.SharedDict["Ctrl_Sp3"].text())
            except Exception as e:
                self.logger.error(e)
                self.last_op_ok= False    
        else:
            
                Warning_str = "Operation can't be performed"
                Reason_str = "Can't connect to JULABO"
                if PopUp:
                    self.Request_msg.emit(Warning_str,Reason_str)
                self.last_op_ok= False
        self.Julabo.lock.release()

    ## Function to power ON/OFF the JULABO
    # implemented as a is a Pyqt slot
    # NOT Executed if:
    # - POWERING ON with JULABO and FNAL info are not updated    
    # - POWERING ON with target temp below DewPoint    
    # - POWERING ON with door not locked    
    # - POWERING ON with door not closed
    # - POWERING OFF with LV ON    
    # - TCP socket is not connected and connection attempt fails
    # Control on cmd execution: read back from instrument            
    @pyqtSlot(bool)    
    def Ctrl_PowerJulabo_Cmd(self,switch, PopUp=True):
        self.last_op_ok= True
        
        if not switch:  # power off
            self.logger.info("WORKER: Powering Julabo OFF")
            if self.SharedDict["LV_on"]:
                Warning_str = "Operation can't be performed"
                Reason_str = "At least one LV channel status is ON"
                if PopUp:
                    self.Request_msg.emit(Warning_str,Reason_str)
                self.last_op_ok= False
                return
                
            self.Julabo.lock.acquire()
            self.logger.debug("WORKER: Sending Julabo cmd" )
            if not self.Julabo.is_connected :
                self.Julabo.connect()
            if self.Julabo.is_connected :
                try:
                    self.Julabo.sendTCP("out_mode_05 0")
                    self.logger.info("WORKER: JULABO cmd sent")
                    self.Julabo.sendTCP("status")
                    reply = self.Julabo.receive()
                    if (reply != "None" and reply != "TCP error"):
                        self.SharedDict["Ctrl_StatusJulabo"].setText(reply)
                    if self.SharedDict["Ctrl_StatusJulabo"].text().find("START")!=-1:
                        self.SharedDict["Ctrl_StatusJulabo"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
                    else:
                        self.SharedDict["Ctrl_StatusJulabo"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ");
                except Exception as e:
                    self.logger.error(e)
                    self.last_op_ok= False    
                        
            self.Julabo.lock.release()
        else:    
            self.logger.info("WORKER: Powering Julabo ON")
            if not (self.SharedDict["Julabo_updated"] and self.SharedDict["FNALBox_updated"]):
                Warning_str = "Operation can't be performed"
                Reason_str = "Julabo and/or FNAL box info are not updated"
                if PopUp:
                    self.Request_msg.emit(Warning_str,Reason_str)
                self.last_op_ok= False
                return
            if float(self.SharedDict["Ctrl_TargetTemp"].text())< float(self.SharedDict["Ctrl_IntDewPoint"].text()):
                Warning_str = "Operation can't be performed"
                Reason_str = "Attempting to start unit with target temperature below internal dew point"
                if PopUp:
                    self.Request_msg.emit(Warning_str,Reason_str)
                self.last_op_ok= False
                return
            if self.SharedDict["Ctrl_StatusLock"].text() != "LOCKED":
                Warning_str = "Operation can't be performed"
                Reason_str = "Attempting to start unit with door magnet not locked"
                if PopUp:
                    self.Request_msg.emit(Warning_str,Reason_str)
                self.last_op_ok= False
                return
            if not (self.SharedDict["Ctrl_StatusDoor"].text() == "CLOSED"):
                Warning_str = "Operation can't be performed"
                Reason_str = "BurnIn door is NOT CLOSED"
                if PopUp:
                    self.Request_msg.emit(Warning_str,Reason_str)
                self.last_op_ok= False
                return
                
            self.Julabo.lock.acquire()
            self.logger.debug("WORKER: Sending Julabo cmd" )
            if not self.Julabo.is_connected :
                self.Julabo.connect()
            if self.Julabo.is_connected :
                try:
                    self.Julabo.sendTCP("out_mode_05 1")
                    self.logger.info("WORKER: JULABO cmd sent")
                    self.Julabo.sendTCP("status")
                    reply = self.Julabo.receive()
                    if (reply != "None" and reply != "TCP error"):
                        self.SharedDict["Ctrl_StatusJulabo"].setText(reply)
                    if self.SharedDict["Ctrl_StatusJulabo"].text().find("START")!=-1:
                        self.SharedDict["Ctrl_StatusJulabo"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
                    else:
                        self.SharedDict["Ctrl_StatusJulabo"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ");
                except Exception as e:
                    self.logger.error(e)
                    self.last_op_ok= False    
            
            else:
            
                Warning_str = "Operation can't be performed"
                Reason_str = "Can't connect to JULABO"
                if PopUp:
                    self.Request_msg.emit(Warning_str,Reason_str)
                self.last_op_ok= False
            self.Julabo.lock.release()
                    
                    

                    
    ## Function to lock/unlock the door (magnet)
    # implemented as a is a Pyqt slot
    # NOT Executed if:
    # - UNLOCK with JULABO/FNAL/M5 info not updated    
    # - UNLOCK with minimal internal temp below EXTERNAL DewPoint
    # - UNLOCK with JULABO ON and taget temp below external dewpoint
    # - status of at least one defined HV channels is ON or UNKNOWN
    # - TCP socket is not connected and connection attempt fails    
    # Control on cmd execution: reply check from FNAL Box    
    @pyqtSlot(bool)    
    def Ctrl_SetLock_Cmd(self,switch, PopUp=True):
        self.last_op_ok= True
        
        lock = "LOCKED" if switch else "UNLOCK"
        cmd = "[5011]" if switch else "[5010]"

        self.logger.info("WORKER: Setting door magnet to: "+lock)
        if (not switch):
            
            if not (self.SharedDict["Julabo_updated"] and self.SharedDict["FNALBox_updated"] and self.SharedDict["M5_updated"]):
                Warning_str = "Operation can't be performed"
                Reason_str = "Julabo, FNAL box or M5 infos are not updated"
                if PopUp:
                    self.Request_msg.emit(Warning_str,Reason_str)
                self.last_op_ok= False
                return
            if (self.SharedDict["Ctrl_StatusJulabo"].text().find("START")!=-1) and (float(self.SharedDict["Ctrl_TargetTemp"].text()) < float(self.SharedDict["Ctrl_ExtDewPoint"].text())):
                Warning_str = "Operation can't be performed"
                Reason_str = "JULABO is ON with target temp below external dew point"
                if PopUp:
                    self.Request_msg.emit(Warning_str,Reason_str)
                self.last_op_ok= False
                return
            if self.SharedDict["Ctrl_LowerTemp"] < float(self.SharedDict["Ctrl_ExtDewPoint"].text()):
                Warning_str = "Operation can't be performed"
                Reason_str = "Internal minimum temperature below external dew point. Retry later"
                if PopUp:
                    self.Request_msg.emit(Warning_str,Reason_str)
                self.last_op_ok= False
                return
            if self.SharedDict["HV_on"]:
                Warning_str = "Operation can't be performed"
                Reason_str = "At least one HV channel status is ON"
                if PopUp:
                    self.Request_msg.emit(Warning_str,Reason_str)
                self.last_op_ok= False
                return
                
        self.FNALBox.lock.acquire()
        self.logger.debug("WORKER: Sending FNAL Box cmd" )
        if not self.FNALBox.is_connected :
            self.FNALBox.connect()
        if self.FNALBox.is_connected :
            try:
                self.FNALBox.sendTCP(cmd)
                self.logger.info("WORKER: FNAL Box cmd sent: " + cmd)
                time.sleep(FNAL_SLEEP_AFTER_TCP)
                reply = self.FNALBox.receive()
                if reply[-3:]=="[*]":
                    self.SharedDict["Ctrl_StatusLock"].setText(lock)
                    self.logger.info("WORKER: Done")
                else:
                    self.SharedDict["Ctrl_StatusLock"].setText("?")
                    self.logger.error("WORKER: uncorrect reply from FNAL Box: "+reply)
                    self.last_op_ok= False

            except Exception as e:
                self.logger.error(e)
                self.SharedDict["Ctrl_StatusLock"].setText("?")    
                self.last_op_ok= False
        
        else:
            Warning_str = "Operation can't be performed"
            Reason_str = "Can't connect to FNAL box"
            if PopUp:
                self.Request_msg.emit(Warning_str,Reason_str)
            self.last_op_ok= False            
        self.FNALBox.lock.release()
        
    ## Function to select LOW/HIGH dry air flow
    # implemented as a is a Pyqt slot
    # NOT Executed if:
    # - TCP socket is not connected and connection attempt fails    
    # Control on cmd execution: reply check from FNAL Box        
    @pyqtSlot(bool)    
    def Ctrl_SetHighFlow_Cmd(self,switch, PopUp=True):
        self.last_op_ok= True
        
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
                time.sleep(FNAL_SLEEP_AFTER_TCP)
                reply = self.FNALBox.receive()
                if reply[-3:]=="[*]":
                    self.SharedDict["Ctrl_StatusFlow"].setText(flow)
                    self.logger.info("WORKER: Done")
                else:
                    self.SharedDict["Ctrl_StatusFlow"].setText("?")
                    self.logger.error("WORKER: uncorrect reply from FNAL Box: "+reply)
                    self.last_op_ok= False

            except Exception as e:
                self.logger.error(e)
                self.SharedDict["Ctrl_StatusFlow"].setText("?")
                self.last_op_ok= False

        else:    
            Warning_str = "Operation can't be performed"
            Reason_str = "Can't connect to FNAL box"
            if PopUp:
                self.Request_msg.emit(Warning_str,Reason_str)
            self.last_op_ok= False                
                    
        self.FNALBox.lock.release()
        
    ## Function to power ON/OFF individual LV channels
    # implemented as a is a Pyqt slot
    # NOT Executed if:
    # - CAEN INFO are not updated
    # - POWER ON with JULABO OFF
    # - one of the slots selected by the user does not have a defined LV channel
    # - trying to switch off a slot with HV ON
    # - trying to switch off a slot with HV OFF but unknown/too high voltage
    # Control on cmd execution: none
    @pyqtSlot(bool)    
    def Ctrl_PowerLV_Cmd(self,switch,Channel_list=[], PopUp=True):
        self.last_op_ok= True
        if PopUp:
            Channel_list.clear()
        power = "On" if switch else "Off"
        if not (self.SharedDict["CAEN_updated"]):
            Warning_str = "Operation can't be performed"
            Reason_str = "CAEN infos are not updated"
            if PopUp:
                self.Request_msg.emit(Warning_str,Reason_str)
            self.last_op_ok= False
            return
        if switch and self.SharedDict["Ctrl_StatusJulabo"].text().find("START")==-1:
            Warning_str = "Operation can't be performed"
            Reason_str = "JULABO is not ON"
            if PopUp:
                self.Request_msg.emit(Warning_str,Reason_str)
            self.last_op_ok= False
            return    
        if len(Channel_list)==0:
            for row in range(NUM_BI_SLOTS):
                if self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_NAME_COL).isSelected():
                    ch_name = self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_NAME_COL).text()
                    if (ch_name == "?"):
                        Warning_str = "Operation can't be performed"
                        Reason_str = "Can't turn OFF LV for slot "+str(row+1)+ " beacause LV ch. name is UNKNOWN"
                        if PopUp:
                            self.Request_msg.emit(Warning_str,Reason_str)
                        self.last_op_ok= False
                        return
                    HV_defined = True if self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_NAME_COL).text() != "?" else False    
                    if (not switch) and  HV_defined and (self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_STAT_COL).text() != "OFF"):  # attempt to power down LV with HV not off
                        Warning_str = "Operation can't be performed"
                        Reason_str = "Can't turn OFF LV for slot "+str(row+1)+ " beacause HV is ON or UNKNOWN"
                        if PopUp:
                            self.Request_msg.emit(Warning_str,Reason_str)
                        self.last_op_ok= False
                        return
                    try:
                        HV_value = float(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_VREAD_COL).text())
                    except Exception as e:
                        self.logger.error(e)
                        Warning_str = "Operation can't be performed"
                        Reason_str = "Can't turn OFF LV for slot "+str(row+1)+ " beacause HV value is invalid"
                        if PopUp:
                            self.Request_msg.emit(Warning_str,Reason_str)
                        self.last_op_ok= False
                        return
                    if (not switch) and  HV_defined and (self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_STAT_COL).text() != "OFF"):  # attempt to power down LV with HV not off
                        Warning_str = "Operation can't be performed"
                        Reason_str = "Can't turn OFF LV for slot "+str(row+1)+ " beacause HV is ON or UNKNOWN"
                        if PopUp:
                            self.Request_msg.emit(Warning_str,Reason_str)
                        self.last_op_ok= False
                        return
                    if (not switch) and  HV_value > HV_ON_THR :  # attempt to power down LV with HV not zero (i.e. still ramping down)
                        Warning_str = "Operation can't be performed"
                        Reason_str = "Can't turn OFF LV for slot "+str(row+1)+ " beacause HV value still too high"
                        if PopUp:
                            self.Request_msg.emit(Warning_str,Reason_str)
                        self.last_op_ok= False
                        return
                    Channel_list.append(ch_name)
                    self.BI_Update_PowerStatus_sig.emit(row,True,power)#isLV=True means LV
                    print("Updating", row, power)
                
        self.logger.info("WORKER: Setting LV "+power+ " for ch " +str(Channel_list))
        for channel in Channel_list:
            self.SendCAENControllerCmd("Turn"+power+",PowerSupplyId:caen,ChannelId:"+channel)    
            
    ## Function to power ON/OFF individual HV channels
    # implemented as a is a Pyqt slot
    # NOT Executed if:
    # - CAEN INFO are not updated
    # - POWER ON with door not CLOSED
    # - one of the slots selected by the user does not have a defined HV channel
    # - trying to switch on a slot with LV OFF
    # Control on cmd execution: none
    @pyqtSlot(bool)    
    def Ctrl_PowerHV_Cmd(self,switch,Channel_list=[],PopUp=True):
        self.last_op_ok= True
        if PopUp:
            Channel_list.clear()
        power = "On" if switch else "Off"
        if not (self.SharedDict["CAEN_updated"] and self.SharedDict["FNALBox_updated"]):
            Warning_str = "Operation can't be performed"
            Reason_str = "CAEN and/or FNAL infos are not updated"
            if PopUp:
                self.Request_msg.emit(Warning_str,Reason_str)
            self.last_op_ok= False
            return
        if switch and (not (self.SharedDict["Ctrl_StatusDoor"].text() == "CLOSED")):
            Warning_str = "Operation can't be performed"
            Reason_str = "BurnIn door is NOT CLOSED"
            if PopUp:
                self.Request_msg.emit(Warning_str,Reason_str)
            self.last_op_ok= False
            return
        
        if len(Channel_list)==0:
            for row in range(NUM_BI_SLOTS):
                if self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_NAME_COL).isSelected():
                    ch_name = self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_NAME_COL).text() 
                    if (ch_name == "?"):
                        Warning_str = "Operation can't be performed"
                        Reason_str = "Can't turn OFF HV for slot "+str(row+1)+ " beacause HV ch. name is UNKNOWN"
                        if PopUp:
                            self.Request_msg.emit(Warning_str,Reason_str)
                        self.last_op_ok= False
                        return
                    if (switch) and (self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_STAT_COL).text() != "ON"):  # attempt to power up HV with LV not on
                        Warning_str = "Operation can't be performed"
                        Reason_str = "Can't turn OFF HV for slot "+str(row+1)+ " beacause LV is OFF or UNKNOWN"
                        if PopUp:
                            self.Request_msg.emit(Warning_str,Reason_str)
                        self.last_op_ok= False
                        return
                    Channel_list.append(ch_name)
                    self.BI_Update_PowerStatus_sig.emit(row,False,power)#isLV=False means HV
                
        self.logger.info("WORKER: Setting HV "+power+ " for ch " +str(Channel_list))
        for channel in Channel_list:
            self.SendCAENControllerCmd("Turn"+power+",PowerSupplyId:caen,ChannelId:"+channel)
    
    ## Function to set indicidual LV/HV channels
    # implemented as a is a Pyqt slot
    # NOT Executed if:
    # - CAEN INFO are not updated
    # - POWER ON with door not CLOSED
    # - one of the slots selected by the user does not have a defined LV/HV setpoint
    # Control on cmd execution: none
    @pyqtSlot(str)    
    def Ctrl_VSet_Cmd(self,VType,Channel_list=[],NewValue_list=[], PopUp=True):
        self.last_op_ok= True
        if PopUp:
            Channel_list.clear()
            NewValue_list.clear()
    
        if VType != "LV" and VType != "HV":
            self.logger.error("WORKER: Received unknow Voltage type string ")
            return
            
        ColOffset = CTRLTABLE_LV_NAME_COL if VType=="LV" else CTRLTABLE_HV_NAME_COL;
        if not (self.SharedDict["CAEN_updated"]):
            Warning_str = "Operation can't be performed"
            Reason_str = "CAEN infos are not updated"
            if PopUp:
                self.Request_msg.emit(Warning_str,Reason_str)
            self.last_op_ok= False
            return
        if len(Channel_list) != len(NewValue_list):
            Warning_str = "Operation can't be performed"
            Reason_str = "Provided ch list and value list doesn not match in length"
            if PopUp:
                self.Request_msg.emit(Warning_str,Reason_str)
            self.last_op_ok= False
            return
            
        if len(Channel_list)==0:
            for row in range(NUM_BI_SLOTS):
                if self.SharedDict["CAEN_table"].item(row,ColOffset).isSelected():
                    ch_name = self.SharedDict["CAEN_table"].item(row,ColOffset).text() 
                    if (ch_name == "?"):
                        Warning_str = "Operation can't be performed"
                        Reason_str = "Can't set LV for  slot "+str(row+1)+ " beacause LV ch. name is UNKNOWN"
                        if PopUp:
                            self.Request_msg.emit(Warning_str,Reason_str)
                        self.last_op_ok= False
                        return
                    if (self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_VSET_COL+ColOffset).text() == "?"): 
                        Warning_str = "Operation can't be performed"
                        Reason_str = "Can't set LV/HV for  slot "+str(row+1)+ " beacause current setpoint is UNKNOWN"
                        if PopUp:
                            self.Request_msg.emit(Warning_str,Reason_str)
                        self.last_op_ok= False
                        return
                    self.SharedDict["WaitInput"]=True
                    Request_str="New " +VType+ " Slot "+str(row+1)
                    ValueNow = 0.0
                    try :
                        ValueNow = float(self.SharedDict["CAEN_table"].item(row,2+ColOffset).text())
                    except Exception as e:
                        self.logger.error(e)
                        
                    if VType == "LV":
                        self.Request_input_dsb.emit(Request_str,ValueNow,MIN_LV,MAX_HV)
                    else:
                        self.Request_input_dsb.emit(Request_str,ValueNow,MIN_HV,MAX_HV)
                        
                    while self.SharedDict["WaitInput"]:
                        time.sleep(0.1)
                    if self.SharedDict["Input"]!=-1:
                        NewValue_list.append(self.SharedDict["Input"])
                        Channel_list.append(ch_name)
        
        self.logger.info("WORKER: Setting LV for ch " +str(Channel_list))
        self.logger.info("WORKER: New values: " +str(NewValue_list))
        for idx,channel in enumerate(Channel_list):
            self.SendCAENControllerCmd("SetVoltage,PowerSupplyId:caen,ChannelId:"+channel+",Voltage:"+str(NewValue_list[idx]))





    ###########################################################################
    ## BI main function and related
    ###########################################################################
    
    
    ## CheckIDs function
    # implemented as a is a Pyqt slot
    @pyqtSlot()            
    def BI_CheckIDs_Cmd(self):
    
    
        self.SharedDict["BI_Status"].setText("CheckIDs Setup")
        self.SharedDict["BI_Action"].setText("Setup")
        
        session_dict={}
        
        session_dict["ActiveSlots"]            = self.SharedDict["BI_ActiveSlots"]
        session_dict["ModuleIDs"]            = self.SharedDict["BI_ModuleIDs"]
        session_dict["fc7ID"]                = "fc7ot2"
        session_dict["Current_ModuleID"]    = "unknown"
        session_dict["fc7Slot"]                = "0"
        session_dict["TestType"]            = "CheckID"
        
        #checking sub-system information
            
        if not (self.SharedDict["CAEN_updated"] and self.SharedDict["FNALBox_updated"] and self.SharedDict["Julabo_updated"]):
            self.logger.error("WORKER: Check IDs procedure failed. JULABO/CAEN/FNAL info are not updated.")
            self.SharedDict["BI_Status"].setText("Failed CheckIDs")
            self.SharedDict["BI_Action"].setText("None")
            self.BI_terminated.emit()
            return
        if not (self.SharedDict["Ctrl_StatusDoor"].text() == "CLOSED"):
            self.logger.error("WORKER: Check IDs procedure failed. Door is not closed.")
            self.SharedDict["BI_Status"].setText("Failed CheckIDs")
            self.SharedDict["BI_Action"].setText("None")
            self.BI_terminated.emit()
            return
        self.logger.info("BurnIn CheckIDs started...")
        
        #selecting slots under test : LV/HV names defined && slot marked as active in BI tab
        
        LV_Channel_list=[]
        HV_Channel_list=[]
        Slot_list=[]
        
        for row in range(NUM_BI_SLOTS):
            LV_ch_name = self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_NAME_COL).text()
            HV_ch_name = self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_NAME_COL).text() 
            if (LV_ch_name != "?" and HV_ch_name != "?" and session_dict["ActiveSlots"][row]):
                LV_Channel_list.append(LV_ch_name)
                HV_Channel_list.append(HV_ch_name)
                Slot_list.append(row)
        
        if len(Slot_list)==0:
            self.logger.error("WORKER: Check IDs procedure failed. Please enable at least one slot...")
            self.SharedDict["BI_Status"].setText("Failed CheckIDs")
            self.SharedDict["BI_Action"].setText("None")
            self.BI_terminated.emit()
            return

        
        self.logger.info("BurnIn CheckIDs active slots: "+str(Slot_list))
        self.logger.info("BurnIn CheckIDs HV names: "+str(HV_Channel_list))
        self.logger.info("BurnIn CheckIDs LV names: "+str(LV_Channel_list))               
        
        PopUp=False
        
        #lock magnet
        self.Ctrl_SetLock_Cmd(True,PopUp)
        if not self.last_op_ok:
            self.logger.error("WORKER: Check IDs procedure failed. can't lock the door.")
            self.SharedDict["BI_Status"].setText("Failed CheckIDs")
            self.SharedDict["BI_Action"].setText("None")
            self.BI_terminated.emit()
            return
            
        #sel SP    
        self.Ctrl_SelSp_Cmd(0,PopUp)
        if not self.last_op_ok:
            self.logger.error("WORKER: Check IDs procedure failed. can't select Julabo SP.")
            self.SharedDict["BI_Status"].setText("Failed CheckIDs")
            self.SharedDict["BI_Action"].setText("None")
            self.BI_terminated.emit()
            return
        
        #put JULABO to 20 degree    
        self.Ctrl_SetSp_Cmd(0,20.0,PopUp)
        if not self.last_op_ok:
            self.logger.error("WORKER: Check IDs procedure failed. Can't set Julabo temperature.")
            self.SharedDict["BI_Status"].setText("Failed CheckIDs")
            self.SharedDict["BI_Action"].setText("None")
            self.BI_terminated.emit()
            return
                
        #start JULABO    
        self.Ctrl_PowerJulabo_Cmd(True,PopUp)
        if not self.last_op_ok:
            self.logger.error("WORKER: Check IDs procedure failed. Can't power ON Julabo.")
            self.SharedDict["BI_Status"].setText("Failed CheckIDs")
            self.SharedDict["BI_Action"].setText("None")
            self.BI_terminated.emit()
            return
        
        ##start LV
        self.SharedDict["BI_Action"].setText("Start LVs")
        self.BI_Update_PowerStatus_sig.emit(-2,True,"ON_dummy")#isLV=True means LV,slot=-2 means all, but command only started
        self.Ctrl_PowerLV_Cmd(True,LV_Channel_list,PopUp)
        if not self.last_op_ok:
            self.logger.error("WORKER: Check IDs procedure failed. Can't start LVs.")
            self.SharedDict["BI_Status"].setText("Failed CheckIDs")
            self.SharedDict["BI_Action"].setText("None")
            self.BI_terminated.emit()
            return
        time.sleep(BI_SLEEP_AFTER_LVSET)
        
        #check all LVs are ON
        for row in Slot_list:
            if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_STAT_COL).text()!="ON"):
                self.logger.error("WORKER: Check IDs procedure failed. LVs check failed.")
                self.SharedDict["BI_Status"].setText("Failed CheckIDs")
                self.SharedDict["BI_Action"].setText("None")
                self.BI_terminated.emit()
                return
        self.BI_Update_PowerStatus_sig.emit(-1,True,"ON_dummy")#isLV=True means LV,slot=-1 means all, update GUI-side  
        
        ##start HV
        #self.SharedDict["BI_Action"].setText("Start HVs")
        #self.Ctrl_PowerHV_Cmd(True,HV_Channel_list,PopUp)
        #if not self.last_op_ok:
        #    self.logger.error("WORKER: Check IDs procedure failed. Can't start HVs.")
        #    self.SharedDict["BI_Status"].setText("Failed CheckIDs")
        #    self.SharedDict["BI_Action"].setText("None")
        #    self.BI_terminated.emit()
        #    return
        #
        #time.sleep(BI_SLEEP_AFTER_HVSET)
        ##check all HVs are ON
        #for row in Slot_list:
        #    if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_STAT_COL).text()!="ON"):
        #        self.logger.error("WORKER: Check IDs procedure failed. HVs check failed.")
        #        self.SharedDict["BI_Status"].setText("Failed CheckIDs")
        #        self.SharedDict["BI_Action"].setText("None")
        #        self.BI_terminated.emit()
        #        return
                
        ##checking IDS
        self.SharedDict["BI_Status"].setText("CheckingIDs")
        self.SharedDict["BI_Action"].setText("Testing")
        for slot in Slot_list:
            self.SharedDict["BI_SUT"].setText(str(slot))
            session_dict["fc7ID"]=self.SharedDict["BI_fc7IDs"][slot]
            session_dict["fc7Slot"]=self.SharedDict["BI_fc7Slots"][slot]
            session_dict["Current_ModuleID"]    = self.SharedDict["BI_ModuleIDs"][slot]
            self.logger.info("BI: Checking ID for BI slot "+str(slot)+": module name "+session_dict["Current_ModuleID"]+", fc7 slot "+session_dict["fc7Slot"]+",board "+session_dict["fc7ID"])
            self.BI_CheckID_isOK_sig.emit(slot,0)#0 means we just started testing
            self.BI_StartTest_Cmd(session_dict)
            if not self.last_op_ok:
                self.SharedDict["BI_Status"].setText("Failed CheckIDs")
                #let's comment these for now and continue testing even if the label is wrong
                #self.SharedDict["BI_Action"].setText("None")
                #self.SharedDict["BI_SUT"].setText("None")
                self.logger.error("WORKER: Check IDs procedure failed. Error returned while checking slot "+str(slot+1))
                self.BI_CheckID_isOK_sig.emit(slot,2)#2 means failure
                #self.BI_terminated.emit()
                #return
            else:
                self.BI_CheckID_isOK_sig.emit(slot,1)#1 means success

        
        self.SharedDict["BI_SUT"].setText("None")
                            
        ##stop HV
        #
        #self.SharedDict["BI_Status"].setText("CheckIDs stopping")
        #self.SharedDict["BI_Action"].setText("Stop HVs")
        #self.Ctrl_PowerHV_Cmd(False,HV_Channel_list,PopUp)
        #if not self.last_op_ok:
        #    self.logger.error("WORKER: Check IDs procedure failed. Can't stop HVs.")
        #    self.SharedDict["BI_Status"].setText("Failed CheckIDs")
        #    self.SharedDict["BI_Action"].setText("None")
        #    self.BI_terminated.emit()
        #    return
        #time.sleep(BI_SLEEP_AFTER_HVSET)
        ##check HV stop
        #for row in Slot_list:
        #    if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_STAT_COL).text()!="OFF"):
        #        self.logger.error("WORKER: Check IDs procedure failed. HVs check failed.")
        #        self.SharedDict["BI_Status"].setText("Failed CheckIDs")
        #        self.SharedDict["BI_Action"].setText("None")
        #        self.BI_terminated.emit()
        #        return
            
        
        #stop LV
        self.SharedDict["BI_Action"].setText("Stop LVs")
        self.BI_Update_PowerStatus_sig.emit(-2,True,"OFF_dummy")#isLV=True means LV,slot=-2 means all, but command only started
        self.Ctrl_PowerLV_Cmd(False,LV_Channel_list,PopUp)
        if not self.last_op_ok:
            self.logger.error("WORKER: Check IDs procedure failed. Can't stop LVs.")
            self.SharedDict["BI_Status"].setText("Failed CheckIDs")
            self.SharedDict["BI_Action"].setText("None")
            self.BI_terminated.emit()
            return
        time.sleep(BI_SLEEP_AFTER_LVSET)
        #check LV stop    
        for row in Slot_list:
            if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_STAT_COL).text()!="OFF"):
                self.logger.error("WORKER: Check IDs procedure failed. LVs check failed.")
                self.SharedDict["BI_Status"].setText("Failed CheckIDs")
                self.SharedDict["BI_Action"].setText("None")
                self.BI_terminated.emit()
                return
        self.BI_Update_PowerStatus_sig.emit(-1,True,"OFF_dummy")#isLV=True means LV,slot=-1 means all, update GUI-side
        
        self.SharedDict["BI_Action"].setText("None")
        self.SharedDict["BI_Status"].setText("Idle")
                
        self.logger.info("BurnIn CheckIDs COMPLETED SUCCESFULLY!")
        self.BI_terminated.emit()
        
        
    ## BI main function
    # implemented as a is a Pyqt slot
    @pyqtSlot()            
    def BI_Start_Cmd(self):
    
        stepAllowed = ["COOL","HEAT","FULLTEST","QUICKTEST","CHECKID","DRYTEST","LV_ON","LV_OFF","HV_ON","HV_OFF","SCANIV"]
        self.SharedDict["BI_Active"]=True
        self.logger.info("Starting BurnIN...")
        
        #creating parameter dictionary for the current session
        session_dict={}
        session_dict["CycleStep"]            = 1
        session_dict["StepList"]            = self.SharedDict["StepList"]
        session_dict["Action"]                = "Undef"
        session_dict["Cycle"]                = 1
        session_dict["Status"]                = "Setup"
        session_dict["LowTemp"]                = self.SharedDict["BI_LowTemp"]
        session_dict["UnderRamp"]            = self.SharedDict["BI_UnderRamp"]
        session_dict["UnderKeep"]            = self.SharedDict["BI_UnderKeep"]
        session_dict["HighTemp"]            = self.SharedDict["BI_HighTemp"]
        session_dict["NCycles"]                = self.SharedDict["BI_NCycles"]
        session_dict["Operator"]            = self.SharedDict["BI_Operator"]
        session_dict["Description"]            = self.SharedDict["BI_Description"]
        session_dict["Session"]                = "-1"
        session_dict["ActiveSlots"]            = self.SharedDict["BI_ActiveSlots"]
        session_dict["ModuleIDs"]            = self.SharedDict["BI_ModuleIDs"]
        session_dict["TestType"]            = "Undef"
        session_dict["Timestamp"]            = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        session_dict["fc7ID"]                = "Undef"
        session_dict["Current_ModuleID"]    = "Undef"
        session_dict["fc7Slot"]                = "Undef"
        session_dict["Current_ModuleHV"]    = "Undef"
        
        
        
        #check if file session already exists (aka a session was stopped or crashed)
        if (os.path.exists("Session.json")):
            self.logger.info("Found session file.")
            self.SharedDict["WaitInput"]=True
            self.Request_confirm_sig.emit("Resume last session?")
            while self.SharedDict["WaitInput"]:
                        time.sleep(0.1)
            if self.SharedDict["Confirmed"]:
                try:
                    with open('Session.json') as json_file:
                        session_dict={}
                        session_dict = json.load(json_file)
                        self.logger.info(session_dict)
                        #updating values in main GUI tab
                        self.BI_Update_GUI_sig.emit(session_dict)
                        self.logger.info("BI :Previous session parameters loaded")
                        self.logger.info("Current Session: "+session_dict["Session"])
                        self.logger.info("Current Cycle: "+str(session_dict["Cycle"]))
                        self.logger.info("Current Step: "+str(session_dict["CycleStep"]))
                        self.logger.info("Current Action: "+session_dict["Action"])
                        session_dict["Status"]    = "Recovery"
                        
                        if len(session_dict["StepList"])==0:
                            self.BI_Abort("Empty cycle description")
                            return    
                        for step in self.SharedDict["StepList"]:
                            if not (step.upper() in stepAllowed):
                                self.BI_Abort("Undefined step in cycle description")
                                return
                        
                except Exception as e:
                    self.logger.error(e)
                    self.logger.error("BI :Error reloading session parameters from Json file")
                    self.BI_Abort("Error while recovering session info. Please start new session")
                    return
            else:
                self.logger.info("Prevoius session overrided. Starting new session")
                if len(session_dict["StepList"])==0:
                    self.BI_Abort("Empty cycle description")
                    return
                for step in self.SharedDict["StepList"]:
                    if not (step.upper() in stepAllowed):
                        self.BI_Abort("Undefined step in cycle description")
                        return
                self.DB_interface.StartSesh(session_dict)
                self.BI_Update_Status_file(session_dict)
                self.BI_Clear_Monitor_sig.emit()

        else:
            self.logger.info("No session file found. Starting new BurnIn session")
            if len(session_dict["StepList"])==0:
                self.BI_Abort("Empty cycle description")
                return    
            for step in self.SharedDict["StepList"]:
                if not (step.upper() in stepAllowed):
                    self.BI_Abort("Undefined step in cycle description")
                    return
            self.DB_interface.StartSesh(session_dict)
            self.BI_Update_Status_file(session_dict)
            self.BI_Clear_Monitor_sig.emit()

        self.SharedDict["TestSession"]=session_dict["Session"]
        
        
        # starting setup/recovery procedure
        
        self.SharedDict["BI_Status"].setText(session_dict["Status"])
            
        self.SharedDict["BI_Action"].setText(session_dict["Action"])
        self.SharedDict["BI_Cycle"].setText(str(session_dict["Cycle"])+" of "+str(session_dict["NCycles"]))
        self.SharedDict["BI_SUT"].setText("None") 
                    
        
        #checking sub-system information
            
        if not (self.SharedDict["CAEN_updated"] and self.SharedDict["FNALBox_updated"] and self.SharedDict["Julabo_updated"]):
            self.BI_Abort("CAEN/FNAL/JULABO infos are not updated")
            return
        if not (self.SharedDict["Ctrl_StatusDoor"].text() == "CLOSED"):
            self.BI_Abort("DOOR is not closed!")
            return
        self.logger.info("BurnIn test started...")
        
        #selecting slots under test : LV/HV names defined && slot marked as active in BI tab
        
        LV_Channel_list=[]
        HV_Channel_list=[]
        Slot_list=[]
        
        for row in range(NUM_BI_SLOTS):
            LV_ch_name = self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_NAME_COL).text()
            HV_ch_name = self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_NAME_COL).text() 
            if (LV_ch_name != "?" and HV_ch_name != "?" and session_dict["ActiveSlots"][row]):
                LV_Channel_list.append(LV_ch_name)
                HV_Channel_list.append(HV_ch_name)
                Slot_list.append(row)

        
        self.logger.info("BurnIn test active slots: "+str(Slot_list))
        self.logger.info("BurnIn test HV names: "+str(HV_Channel_list))
        self.logger.info("BurnIn test LV names: "+str(LV_Channel_list))               
        
        PopUp=False
        
        #lock magnet
        if not self.BI_Action(self.Ctrl_SetLock_Cmd,True,True,PopUp):
            return
            
        #start high flow if needed
        try:
            dp = float(self.SharedDict["Ctrl_IntDewPoint"].text())
        except Exception as e:
            dp=0.0
        if dp > BI_HIGHFLOW_THRESHOLD and self.SharedDict["Ctrl_StatusFlow"].text()!="HIGH":
            if not self.BI_Action(self.Ctrl_SetHighFlow_Cmd,True, True,PopUp):
                return
            
        #sel SP    
        if not self.BI_Action(self.Ctrl_SelSp_Cmd,True,0,PopUp):
            return
                
        #start JULABO    
        if not self.BI_Action(self.Ctrl_PowerJulabo_Cmd,True,True,PopUp):
            return
        
        ###start LV
        #self.SharedDict["BI_Action"].setText("Start LVs")
        #if not self.BI_Action(self.Ctrl_PowerLV_Cmd,True,True,LV_Channel_list,PopUp):
        #    return
        #time.sleep(BI_SLEEP_AFTER_LVSET)
        #
        ##check all LVs are ON
        #for row in Slot_list:
        #    if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_STAT_COL).text()!="ON"):
        #        self.BI_Abort("BI aborted: some LVs was not turned ON")
        #        return
        #
        ##start HV
        #self.SharedDict["BI_Action"].setText("Start HVs")
        #if not self.BI_Action(self.Ctrl_PowerHV_Cmd,True,True,HV_Channel_list,PopUp):
        #    return
        #
        #time.sleep(BI_SLEEP_AFTER_HVSET)
        ##check all HVs are ON
        #for row in Slot_list:
        #    if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_STAT_COL).text()!="ON"):
        #        self.BI_Abort("BI aborted: some HVs was not turned ON")
        #        return
            
        
        session_dict["Status"] = "Cycling"
        self.SharedDict["BI_Status"].setText(session_dict["Status"])

        NCycles    = session_dict["NCycles"]
        ######cycle start
        if (session_dict["Status"]=="Recovery"):
            self.logger.info("BI: recovered from cycle "+str(session_dict["Cycle"]) + " of "+str(NCycles)+" @ step "+session_dict["CycleStep"])
        
        while(session_dict["Cycle"]-1 < NCycles):
            while session_dict["CycleStep"]-1 < len(session_dict["StepList"]):
            
                session_dict["Action"]=session_dict["StepList"][session_dict["CycleStep"]-1]
                self.logger.info("BI: cycle "+str(session_dict["Cycle"]) + " of "+str(NCycles))
                self.SharedDict["BI_Step"].setText(str(session_dict["CycleStep"])+" of "+str(len(session_dict["StepList"])))
                
                if (session_dict["Action"].upper()=="COOL"):
                    self.BI_Update_Status_file(session_dict)
                    self.logger.info("BI: ramping down...")
                    self.SharedDict["BI_Action"].setText("Cooling")
                    self.SharedDict["BI_SUT"].setText("None") 
                    if float(self.SharedDict["LastFNALBoxTemp0"].text()) > session_dict["LowTemp"]:  #expected
                        if not self.BI_Action(self.BI_GoLowTemp,True,session_dict,session_dict["LowTemp"]):
                            self.logger.info("BI: cooling")
                            return
                    else:
                        if not self.BI_Action(self.BI_GoHighTemp,True,session_dict,session_dict["LowTemp"]):
                            return
                    
                if (session_dict["Action"].upper()=="HEAT"):
                    self.BI_Update_Status_file(session_dict)
                    self.logger.info("BI: going to high temp")
                    self.SharedDict["BI_Action"].setText("Heating")
                    self.SharedDict["BI_SUT"].setText("None") 
                    if float(self.SharedDict["LastFNALBoxTemp0"].text()) < session_dict["HighTemp"]:  #expected
                        self.logger.info("BI: heating")
                        if not self.BI_Action(self.BI_GoHighTemp,True,session_dict,session_dict["HighTemp"]):
                            return
                    else:
                        if not self.BI_Action(self.BI_GoLowTemp,True,session_dict,session_dict["HighTemp"]):
                            return
                    
                if (session_dict["Action"].upper()=="FULLTEST" or session_dict["Action"].upper()=="CHECKID" or session_dict["Action"].upper()=="QUICKTEST" or session_dict["Action"].upper()=="DRYTEST"):
                    self.BI_Update_Status_file(session_dict)
                    self.logger.info("BI: testing...")
                    self.SharedDict["BI_Action"].setText(session_dict["Action"]+"  Module test")
                    self.SharedDict["BI_TestActive"]=True
                    session_dict["TestType"]=session_dict["Action"]
                    for slot in Slot_list:
                        session_dict["fc7ID"]=self.SharedDict["BI_fc7IDs"][slot]
                        session_dict["fc7Slot"]=self.SharedDict["BI_fc7Slots"][slot]
                        session_dict["Current_ModuleID"]    = self.SharedDict["BI_ModuleIDs"][slot]
                        self.SharedDict["BI_SUT"].setText(str(slot+1)) 
                        self.logger.info("BI: testing BI slot "+str(slot)+": module name "+session_dict["Current_ModuleID"]+", fc7 slot "+session_dict["fc7Slot"]+",board "+session_dict["fc7ID"])
                        self.BI_CheckID_isOK_sig.emit(slot,0)#0 means we just started testing
                        if not self.BI_Action(self.BI_StartTest_Cmd,False,session_dict):
                            self.BI_CheckID_isOK_sig.emit(slot,2)#2 means failure
                            return
                        else:
                            self.BI_CheckID_isOK_sig.emit(slot,1)#1 means success
                            
                    self.SharedDict["BI_TestActive"]=False
                    session_dict["TestType"]="Undef"
                    
                if (session_dict["Action"].upper()=="SCANIV"):
                    self.BI_Update_Status_file(session_dict)
                    self.logger.info("BI: IV scan...")
                    self.SharedDict["BI_Action"].setText("IV scan")
                    self.SharedDict["BI_TestActive"]=True
                    for slot in Slot_list:
                        session_dict["Current_ModuleID"]    = self.SharedDict["BI_ModuleIDs"][slot]
                        session_dict["Current_ModuleHV"]    = HV_Channel_list[slot]
                        self.SharedDict["BI_SUT"].setText(str(slot+1)) 
                        self.logger.info("BI: IV scan for slot "+str(slot)+": module name "+session_dict["Current_ModuleID"])
                        if not self.BI_Action(self.BI_StartIV_Cmd,False,session_dict):
                                return
                    self.SharedDict["BI_TestActive"]=False
                            
                if (session_dict["Action"].upper()=="LV_ON"):
                    self.BI_Update_Status_file(session_dict)
                    self.logger.info("BI: Starting LVs")
                    self.SharedDict["BI_Action"].setText("Starting LVs")
                    self.SharedDict["BI_SUT"].setText("None") 
                    self.BI_Update_PowerStatus_sig.emit(-2,True,"ON_dummy")#isLV=True means LV,slot=-2 means all, but command only started
                    if not self.BI_Action(self.Ctrl_PowerLV_Cmd,True,True,LV_Channel_list,PopUp):
                        return
                    time.sleep(BI_SLEEP_AFTER_LVSET)
                    #check all LVs are ON
                    for row in Slot_list:
                        if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_STAT_COL).text()!="ON"):
                            self.BI_Abort("BI aborted: some LVs was not turned ON")
                            return
                    self.BI_Update_PowerStatus_sig.emit(-1,True,"ON_dummy")#isLV=True means LV,slot=-1 means all, update GUI-side
                
                            
                if (session_dict["Action"].upper()=="LV_OFF"):
                    self.BI_Update_Status_file(session_dict)
                    self.logger.info("BI: Stopping LVs")
                    self.SharedDict["BI_Action"].setText("Stopping LVs")
                    self.SharedDict["BI_SUT"].setText("None") 
                    self.BI_Update_PowerStatus_sig.emit(-2,True,"OFF_dummy")#isLV=True means LV,slot=-2 means all, but command only started
                    if not self.BI_Action(self.Ctrl_PowerLV_Cmd,True,False,LV_Channel_list,PopUp):
                        return
                    time.sleep(BI_SLEEP_AFTER_LVSET)
                    #check all LVs are OFF
                    for row in Slot_list:
                        if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_STAT_COL).text()!="OFF"):
                            self.BI_Abort("BI aborted: some LVs was not turned OFF")
                            return
                    self.BI_Update_PowerStatus_sig.emit(-1,True,"OFF_dummy")#isLV=True means LV,slot=-1 means all, update GUI-side
                            
                if (session_dict["Action"].upper()=="HV_ON"):
                    self.BI_Update_Status_file(session_dict)
                    self.logger.info("BI: Starting HVs")
                    self.SharedDict["BI_Action"].setText("Starting HVs")
                    self.SharedDict["BI_SUT"].setText("None")
                    self.BI_Update_PowerStatus_sig.emit(-2,False,"ON_dummy")#isLV=False means HV,slot=-2 means all, but command only started
                    if not self.BI_Action(self.Ctrl_PowerHV_Cmd,True,True,HV_Channel_list,PopUp):
                        return
                    time.sleep(BI_SLEEP_AFTER_HVSET)
                    #check all HVs are ON
                    for row in Slot_list:
                        if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_STAT_COL).text()!="ON"):
                            self.BI_Abort("BI aborted: some HVs was not turned ON")
                            return
                    self.BI_Update_PowerStatus_sig.emit(-1,False,"ON_dummy")#isLV=False means HV,slot=-1 means all, update GUI-side
                            
                if (session_dict["Action"].upper()=="HV_OFF"):
                    self.BI_Update_Status_file(session_dict)
                    self.logger.info("BI: Stopping HVs")
                    self.SharedDict["BI_Action"].setText("Stopping HVs")
                    self.SharedDict["BI_SUT"].setText("None")
                    self.BI_Update_PowerStatus_sig.emit(-2,False,"OFF_dummy")#isLV=False means HV,slot=-2 means all, but command only started
                    if not self.BI_Action(self.Ctrl_PowerHV_Cmd,True,False,HV_Channel_list,PopUp):
                        return
                    time.sleep(BI_SLEEP_AFTER_HVSET)
                    #check all HVs are OFF
                    for row in Slot_list:
                        if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_STAT_COL).text()!="OFF"):
                            self.BI_Abort("BI aborted: some LVs was not turned OFF")
                            return
                    self.BI_Update_PowerStatus_sig.emit(-1,False,"OFF_dummy")#isLV=False means HV,slot=-1 means all, update GUI-side
                    
                session_dict["CycleStep"]=session_dict["CycleStep"]+1
                
            session_dict["CycleStep"]=1
            self.logger.info("BI: ended cycle "+str(session_dict["Cycle"]) + " of "+str(NCycles))
            session_dict["Cycle"]=session_dict["Cycle"]+1
        
        if (os.path.exists("Session.json")):        
            os.remove("Session.json")
            self.logger.info("BI: Session json file deleted")
        else:
            self.logger.info("BI: Could not locate session json file")
        
        self.SharedDict["BI_Status"].setText("Stopping")
        self.SharedDict["BI_SUT"].setText("None") 
        
        #stop HV
        self.SharedDict["BI_Action"].setText("Stop HVs")
        if not self.BI_Action(self.Ctrl_PowerHV_Cmd,True,False,HV_Channel_list,PopUp):
            return
        time.sleep(BI_SLEEP_AFTER_HVSET)
        #check HV stop
        for row in Slot_list:
            if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_STAT_COL).text()!="OFF"):
                self.BI_Abort("BI aborted: some LVs was not turned OFF")
                return
            
        
        #stop LV
        self.SharedDict["BI_Action"].setText("Stop LVs")
        if not self.BI_Action(self.Ctrl_PowerLV_Cmd,True,False,LV_Channel_list,PopUp):
            return
        time.sleep(BI_SLEEP_AFTER_LVSET)
        #check LV stop    
        for row in Slot_list:
            if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_STAT_COL).text()!="OFF"):
                self.BI_Abort("BI aborted: some HVs was not turned OFF")
                return
                
        #put JULABO to 20 degree    
        self.SharedDict["BI_Action"].setText("Closing")
        if not self.BI_Action(self.Ctrl_SetSp_Cmd,True,0,20.0,PopUp):
            return    
        
        #lower dry air flow
        if self.SharedDict["Ctrl_StatusFlow"].text()=="HIGH":
            if not self.BI_Action(self.Ctrl_SetHighFlow_Cmd,True, False,PopUp):
                return
                
        self.logger.info("BurnIn test COMPLETED SUCCESFULLY!")
        self.SharedDict["BI_Active"]=False
        self.SharedDict["BI_Status"].setText("Idle")
        self.SharedDict["BI_Action"].setText("None")
        self.SharedDict["BI_StopRequest"]=False
        if os.path.exists("Session.json"):
            os.remove("Session.json")
        self.BI_terminated.emit()
    
    ## BI Abort function    
    def BI_Abort(self,Reason_str):
    
            Warning_str = "BURN IN test failed"
            self.SharedDict["BI_Status"].setText("Aborted")
            #self.Request_msg.emit(Warning_str,Reason_str)
            self.logger.info("WORKER: BI aborted"+ Reason_str )
            self.SharedDict["BI_Active"]=False
            self.SharedDict["BI_StopRequest"]=False
            self.SharedDict["BI_TestActive"]=False
            self.BI_terminated.emit()
        
    
    ## BI Action function. used to execute a defined operation.        
    def BI_Action(self,Action,abort_if_fail, *args):
        retry=BI_ACTION_RETRIES
        while retry:
            Action(*args)
            if self.SharedDict["BI_StopRequest"]:
                self.BI_Abort("BI: aborted for user or Supervisor request")
                return False
            if not (self.last_op_ok):
                self.logger.warning("BI: failed to do action...new try in 10 sec")
                time.sleep(BI_ACTION_RETRY_SLEEP)
                retry=retry-1
            else:
                return True
        if abort_if_fail:
            self.BI_Abort("BI: failed to do action ("+str(BI_ACTION_RETRIES)+" times)...aborting")
            return False
        else:
            self.logger.warning("BI: failed to do action ("+str(BI_ACTION_RETRIES)+" times)...but going ahead with test")
            return True

    ## BI function to ramp down in temp
    def BI_GoLowTemp(self,session_dict,LowTemp):
        self.BI_GoSelectedTemp(session_dict,LowTemp,isCooling=True,PopUp=False)
            
    ## BI function to ramp up in temp
    def BI_GoHighTemp(self,session_dict,HighTemp):
        self.BI_GoSelectedTemp(session_dict,HighTemp,isCooling=False,PopUp=False)
        
    ## BI generic function to change temp
    def BI_GoSelectedTemp(self,session_dict,SelectedTemp,isCooling,PopUp=False):

        TempTolerance     = BI_TEMP_TOLERANCE
        TempRampOffset    = session_dict["UnderRamp"]
        TempMantainOffset = session_dict["UnderKeep"]

        self.last_op_ok= True
        last_step=False # assume we cannot go directly to the target temperature
        
        nextTemp = 0.0
        #initialise and keep if heating
        TargetTemp = SelectedTemp+TempMantainOffset #aim slightly above target
        TempMargin = - TempMantainOffset
        verb="heating"
        if isCooling:
            TargetTemp = SelectedTemp-TempRampOffset #aim below target
            TempMargin = TempRampOffset
            verb="cooling"
        
        #cooling loops
        while (not last_step):
            try:
                #acquire dewpoint, must be done at every step
                dewPoint = float(self.SharedDict["Ctrl_IntDewPoint"].text())
            except Exception as e:
                self.logger.error(e)
                self.last_op_ok= False
                return
            
            if (TargetTemp> dewPoint):#if the temperature we aim for is above the dewpoint everything is fine and there will be no further steps; this is always true if heating
                nextTemp = TargetTemp
                self.logger.info("BI: target temp above dew point - OK!")
                last_step = True
            else: #if not, we aim slightly above the dewpoint and rise flow (FT: should this really be hardcoded?)
                nextTemp = dewPoint+1
                self.logger.info("BI: target temp below dew point, going to dew point and switching to high flow.")
                if not self.BI_Action(self.Ctrl_SetHighFlow_Cmd,True, True,PopUp):
                    return

            #set to hold temperature at the target nextTemp
            if not self.BI_Action(self.Ctrl_SetSp_Cmd,True,0,nextTemp,PopUp):
                self.last_op_ok= False
                return    

            #while changing temperature, check if we reach the target and adjust the flow
            while(True):
                try:
                    self.logger.info("BI: %s to target temperature..."%(verb))
                    dewPoint = float(self.SharedDict["Ctrl_IntDewPoint"].text())
                    #dry airflow increases heat and lowers humidity
                    #I want high flow when warming up or when the dew point is too high during the cooling phase
                    #If the dew point is sufficiently low and I'm cooling, switch to low flow
                    #If we are not at the last step, then it's obviously the former and lowering humidity takes priority
                    if last_step and isCooling:
                        if self.SharedDict["Ctrl_StatusFlow"].text()=="HIGH":
                            self.logger.info("BI: setting low flow....")    
                            if not self.BI_Action(self.Ctrl_SetHighFlow_Cmd,True,False,PopUp):
                                return
                    elif self.SharedDict["Ctrl_StatusFlow"].text()!="HIGH":
                        self.logger.info("BI: setting high flow....")    
                        if not self.BI_Action(self.Ctrl_SetHighFlow_Cmd,True,True,PopUp):
                            return
                    #
                    if (abs(float(self.SharedDict["LastFNALBoxTemp0"].text())-(nextTemp+TempMargin)) < TempTolerance):
                        #this happens when we reach SelectedTemp when heating or at the last cooling step, or TempRampOffset above target at intermediate cooling steps
                        break
                    if self.SharedDict["BI_StopRequest"]:
                        self.last_op_ok= False
                        return    
                    if not (self.SharedDict["CAEN_updated"] and self.SharedDict["FNALBox_updated"] and self.SharedDict["Julabo_updated"]):
                        if not (self.SharedDict["CAEN_updated"]):
                            self.logger.info("BI: CAEN info not updated while %s..."%(verb))
                        if not (self.SharedDict["FNALBox_updated"]):
                            self.logger.info("BI: FNAL info not updated while %s..."%(verb))
                        if not (self.SharedDict["Julabo_updated"]):
                            self.logger.info("BI: Julabo info not updated while %s..."%(verb))
                        self.last_op_ok= False
                        return
                    time.sleep(BI_SLEEP_AFTER_TEMP_CHECK)
                except Exception as e:
                    self.logger.error(e)
                    self.last_op_ok= False
                    return
            #end while(True)
        #end while (not last_step)

        #set high flow in case it was set to low
        if not self.BI_Action(self.Ctrl_SetHighFlow_Cmd,True,True,PopUp):
            return
        # set target temperature mantain
        self.logger.info("BI: keep temperature ....")
        if not self.BI_Action(self.Ctrl_SetSp_Cmd,True,0,SelectedTemp-TempMantainOffset,PopUp):
            self.last_op_ok= False
            return
               
    def BI_Update_Status_file(self,session_dict):
    
        with open("Session.json", "w") as outfile: 
            json.dump(session_dict, outfile)


    def BI_StartIV_Cmd(self, session_dict):
    
        module = session_dict["Current_ModuleID"]
        HV_ch = session_dict["Current_ModuleHV"]
        self.logger.info("Starting IV scan on module "+module+" on HV channel "+HV_ch+" ...")
        self.last_op_ok= True
        
        cmd = "python3 measure_iv_curve.py --channel "+HV_ch+ " --scan-type "+ self.IV_scanType+ " --delay "+ self.IV_delay +" --settling-time "+ self.IV_settlingTime+  " -–module_name "+ module 
        self.logger.info("Executing command: " + cmd)
        
        try:
            proc = subprocess.Popen(cmd.split(), cwd=self.BIcwd,stdout=subprocess.PIPE, stderr=subprocess.STDOUT)                                    
            
            while(proc.returncode==None):
                
                if self.SharedDict["BI_StopRequest"]:
                    self.logger.error("WORKER: Aborting module IV scan on external request")
                    proc.kill()
                    self.last_op_ok= False
                    return
                try:
                    outs, errs = proc.communicate(timeout=TEST_PROCESS_SLEEP)
                    self.logger.info("BI IV SCAN SUBPROCESS: "+outs.decode())
                    #self.logger.error("BI TEST SUBPROCESS: "+errs.decode())
                    break
                except subprocess.TimeoutExpired:
                    self.logger.info("WORKER: Waiting IV SCAN completion....")
                    #while True:
                    #    inline = proc.stdout.readline()
                    #    if not inline:
                    #        break
                    #    self.logger.info("BI TEST SUBPROCESS: "+inline.decode())
            
            if proc.returncode ==0:
                self.logger.info("Module IV Scan succesfully completed with exit code "+str(proc.returncode))
            elif proc.returncode==None:
                self.logger.info("Module IV Scan succesfully completed with exit code NONE")
            else:
                self.logger.error("Module IV Scan failed with exit code "+str(proc.returncode))
                self.last_op_ok= False
                
        except Exception as e:
            self.logger.error("Erro during IV Scan")
            self.logger.error(e)
            self.last_op_ok= False
            
            
    def BI_StartTest_Cmd(self, session_dict):
        module = session_dict["Current_ModuleID"]
        self.logger.info("Starting module "+module+" test...")
        session=self.SharedDict["TestSession"]
        
        if session_dict["TestType"]=="DryTest":
            self.logger.info("Dry run. Just waiting 60 s.")
            time.sleep(60)
            return True 
        
        test_type = "readOnlyID"    
        if session_dict["TestType"]=="FullTest":
            test_type = "PSfullTest"
        elif session_dict["TestType"]=="QuickTest":
            test_type = "PSquickTest"
        elif session_dict["TestType"]=="CheckID":
            test_type = "readOnlyID"
        else :
            self.logger.warning("Unrecognized test type: "+test_type+". Checking ID")
        
        self.logger.info("Test type: "+test_type)
        
        fc7Slot = session_dict["fc7Slot"]
        fc7ID = session_dict["fc7ID"]
        
        self.last_op_ok= True
        
        #create non-blocking process
        if self.Ph2_ACF_version=="latest":
            cmd = "python3 moduleTest.py -c "+test_type+ " --board "+ fc7ID + " --slot "+ fc7Slot +" --module "+ module+  " --session " + session
        else:
            cmd = "python3 moduleTest.py -c "+test_type+ " --board "+ fc7ID + " --slot "+ fc7Slot +" --module "+ module+  " --session " + session+" --version "+ self.Ph2_ACF_version
        
        self.logger.info("Executing command: " + cmd)
        try:    
            proc = subprocess.Popen(cmd.split(), cwd=self.BIcwd,stdout=subprocess.PIPE, stderr=subprocess.STDOUT)                                    
            
            while(proc.returncode==None):
                
                if self.SharedDict["BI_StopRequest"]:
                    self.logger.error("WORKER: Aborting module test on external request")
                    proc.kill()
                    self.last_op_ok= False
                    return
                try:
                    outs, errs = proc.communicate(timeout=TEST_PROCESS_SLEEP)
                    self.logger.info("BI TEST SUBPROCESS: "+outs.decode())
                    #self.logger.error("BI TEST SUBPROCESS: "+errs.decode())
                    break
                except subprocess.TimeoutExpired:
                    self.logger.info("WORKER: Waiting test completion....")
                    #while True:
                    #    inline = proc.stdout.readline()
                    #    if not inline:
                    #        break
                    #    self.logger.info("BI TEST SUBPROCESS: "+inline.decode())
            
            if proc.returncode ==0:
                self.logger.info(session_dict["TestType"]+" Module test succesfully completed with exit code "+str(proc.returncode))
            elif proc.returncode==None:
                self.logger.info(session_dict["TestType"]+" Module test succesfully completed with exit code NONE")
            else:
                self.logger.error(session_dict["TestType"]+" Module test failed with exit code "+str(proc.returncode))
                self.last_op_ok= False
                
        except Exception as e:
            self.logger.error("Erro while testing")
            self.logger.error(e)
            self.last_op_ok= False
                    
    
    @pyqtSlot(bool)                
    def MT_StartTest_Cmd(self, dry=False, PupUp=False):
            self.logger.info("Starting module test...Please wait till completion")
            if PupUp:
                msg = QMessageBox()
                msg.setWindowTitle("Module test ongoing. Please wait...")
                msg.show()
            session=self.SharedDict["TestSession"]
            if dry:
                result = subprocess.run(["python3", "moduleTest.py", "--board", "fc7ot2", "--slot", "0" ,"--module", "PS_26_05-IPG_00102",  "--session", session, "--useExistingModuleTest","T2023_12_04_16_26_11_224929"],
                                                    cwd=self.BIcwd)
            else:
                result = subprocess.run(["python3", "moduleTest.py", "--board", "fc7ot2", "--slot", "0" ,"--module", "PS_26_05-IPG_00102",  "--session", session],
                                                    cwd=self.BIcwd)
            self.logger.info(result.stdout)
            self.logger.error(result.stderr)
            self.logger.info("Module test completed!")
            
    
    def MT_UploadDB_Cmd(self):
        pass
