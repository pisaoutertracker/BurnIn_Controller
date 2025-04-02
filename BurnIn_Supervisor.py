import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject, pyqtSignal
import time
from datetime import datetime
import json
from __Constant import *

from MQTT_interface import *


class BurnIn_Supervisor(QObject):

    BI_Abort_sig = pyqtSignal()

    def __init__(self,configDict,logger, SharedDict, Julabo, CAENController):
    
        super(BurnIn_Supervisor,self).__init__();
        self.configDict=configDict
        self.logger = logger
        self.logger.info("SUPERVISOR: Supervisor class initialized")
        
        self.MQTT =  MQTT_interface(configDict,logger,"BurnIn_supervisor")
        self.SharedDict = SharedDict
        self.Julabo = Julabo
        self.CAENController = CAENController
        
        self.Enabled=True
        EnablePar = configDict.get(("Supervisor","Enabled"),"NOKEY")
        if EnablePar == "NOKEY":
            self.logger.warning("Supervisor analble parameter not found. Enabled by default default")
        if EnablePar == "False":
            self.Enabled=False
                
            
            
    def run(self):
        self.logger.info("SUPERVISOR: Attempting first connection to MQTT server...")
        self.MQTT.connect()
        self.logger.info("SUPERVISOR: SUPERVISOR thread started...waiting "+ str(SUPERVISOR_START_DELAY) +"s")
        time.sleep(SUPERVISOR_START_DELAY)
        
        self.logger.info("SUPERVISOR: SUPERVISOR is now armed")
            
        while(self.Enabled):
            
            if self.SharedDict["Quitting"]:
                return
        
            self.SharedDict["LastSupervision"].setStyleSheet("");
            self.SharedDict["LastSupervision"].setText(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            
            #MQTT connection cycle
            if not self.MQTT.is_subscribed:
                self.logger.info("MONITOR: Attempting first connection to MQTT server...")
                self.MQTT.connect()
                if self.MQTT.is_connected :
                    self.SharedDict["MQTTSConn"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
                    self.SharedDict["MQTTSConn"].setText("Connected")
            else:
                if self.MQTT.is_connected :
                    self.SharedDict["MQTTSConn"].setStyleSheet("color: rgb(0, 170, 0);font: 9pt ");
                    self.SharedDict["MQTTSConn"].setText("Connected")
                else:
                    self.SharedDict["MQTTSConn"].setStyleSheet("color: rgb(255, 0, 0);font: 9pt ");
                    self.SharedDict["MQTTSConn"].setText("Disconnected")

            #retrieve power status
            power_on = False
            for i in range (10):
                if self.SharedDict["CAEN_table"].item(i,CTRLTABLE_LV_STAT_COL).text() == "ON":
                    power_on = True    

            
            #        LV                temp(FNAL)        Action
            #
            #        ?                warning            alert
            #        ?                critical        alert
            #        ON                ?                alert/action
            #        ON                warning            alert
            #        ON                critical        alert/action
            #        OFF                warning            alert
            #        OFF                critical        alert

            #overtemperature checks
            if  not self.SharedDict["CAEN_updated"]:
                if  self.SharedDict["Ctrl_HigherTemp"] > TEMP_ERROR:
                    self.send_alert("CRITICAL: Temperature above Critical threshold ("+str(TEMP_ERROR)+")AND no info from CAEN")
                elif self.SharedDict["Ctrl_HigherTemp"]> TEMP_WARNING:
                    self.send_alert("WARNING: Temperature above Warning threshold ("+str(TEMP_WARNING)+")AND no info from CAEN")
            else:
                if power_on:
                    if not self.SharedDict["FNALBox_updated"]:
                        self.send_alert("CRITICAL: Power is on but no info about temperature")
                        self.HV_shutdown()
                        self.LV_shutdown()
                    else:
                        if  self.SharedDict["Ctrl_HigherTemp"] > TEMP_ERROR:
                            self.send_alert("CRITICAL: Temperature above Critical threshold ("+str(TEMP_ERROR)+"). Shutting down HV and LVs.")
                            self.HV_shutdown()
                            self.LV_shutdown()
                        elif self.SharedDict["Ctrl_HigherTemp"]> TEMP_WARNING:
                            self.send_alert("WARNING: Temperature above Warning threshold ("+str(TEMP_WARNING)+")")
                            self.logger.warning("SUPERVISOR: Temperature above Warning threshold ("+str(TEMP_WARNING)+")")
                else:
                    if  self.SharedDict["Ctrl_HigherTemp"] > TEMP_ERROR:
                        self.send_alert("CRITICAL: Temperature above Critical threshold ("+str(TEMP_ERROR)+") but LV are OFF!")
                    elif self.SharedDict["Ctrl_HigherTemp"]> TEMP_WARNING:
                        self.send_alert("WARNING: Temperature above Warning threshold ("+str(TEMP_WARNING)+") but LV are OFF")
            

            
            #        Julabo            temp(FNAL)/door(FNAL)      M5            Action
            #                            
            #        ON                ?/?                            x            alert/action
            #        ON                critical/closed                x            alert/action
            #        ?                critical/closed                x            alert
            #        ON                critical/open            critical        alert/action
            #        ?                critical/open            critical        alert
            #        ON                critical/open                ?            alert/action            
            
            #undertemperature checks
            if not self.SharedDict["FNALBox_updated"]:
                if self.SharedDict["Julabo_updated"] and self.SharedDict["Ctrl_StatusJulabo"].text().find("START")!=-1:
                    self.send_alert("WARNING: Julabo on but no temperature/dew point info")
                    self.JULABO_safeTemp()
            else:
                if self.SharedDict["Ctrl_StatusDoor"].text()=="CLOSED":
                    if self.SharedDict["Ctrl_LowerTemp"] < float(self.SharedDict["LastFNALBoxDP"].text()):
                        if self.SharedDict["Julabo_updated"] and self.SharedDict["Ctrl_StatusJulabo"].text().find("START")!=-1:
                            self.send_alert("WARNING: Door closed, internal emperature below internal Dew Point")
                            self.JULABO_safeTemp()
                        elif not self.SharedDict["Julabo_updated"]:
                            self.send_alert("WARNING: Door closed, internal emperature below internal Dew Point but no control on JULABO. PLEASE ACT!")
                            
                elif self.SharedDict["Ctrl_StatusDoor"].text()=="OPEN":
                    if self.SharedDict["M5_updated"] :
                        if self.SharedDict["Ctrl_LowerTemp"] < float(self.SharedDict["LastM5DP"].text()):
                            if self.SharedDict["Julabo_updated"] and self.SharedDict["Ctrl_StatusJulabo"].text().find("START")!=-1:
                                self.send_alert("WARNING: Door open with Julabo on, internal temperature below external Dew Point")
                                self.JULABO_safeTemp()
                            else:
                                self.send_alert("WARNING: Door open, internal temperature below external Dew Point, no or inconsistent info from JULABO. PLEASE ACT!")
                    elif self.SharedDict["Julabo_updated"] and self.SharedDict["Ctrl_StatusJulabo"].text().find("START")!=-1:
                        self.send_alert("WARNING: Door open and Julabo on, but no external temperature/dew point info")
                        self.JULABO_safeTemp()
        
    
            self.logger.debug("SUPERVISOR: SUPERVISOR cycle done")
            time.sleep(SUPERVISOR_SLEEP)
        
        self.logger.info("SUPERVISOR: DISABLED as per yaml configuration")
        
    def send_alert(self, text):
    
        self.logger.error("SUPERVISOR: " + text)
        if self.MQTT.is_connected:
            self.MQTT.publish("/alarm","BurnIn: "+text)
        else:
            self.logger.error("SUPERVISOR: MQTT disconnected, can't publish alert!")
            
    def HV_shutdown(self):
        if self.SharedDict["BI_Active"]: 
            self.BI_Abort()
            
        # cycling to switch off HVs        
        repeat= True
        while(repeat):
            repeat= False
            Channel_list=[]
            for row in range(NUM_BI_SLOTS):
                ch_name = self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_NAME_COL).text() 
                if (ch_name != "?"):
                    Channel_list.append(ch_name)        
            self.logger.info("Supervisor: Setting HV OFF for ch " +str(Channel_list))
            for channel in Channel_list:
                self.SendCAENControllerCmd("TurnOff,PowerSupplyId:caen,ChannelId:"+channel)    
            
            time.sleep(30)
            
            for row in range(NUM_BI_SLOTS):
                ch_name = self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_NAME_COL).text() 
                if (ch_name != "?"):
                    if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_STAT_COL).text()!="OFF"):
                        repeat=True
                        
    def LV_shutdown(self):
        if self.SharedDict["BI_Active"]: 
            self.BI_Abort()
        
        
        # cycling to switch off LVs        
        repeat= True
        while(repeat):    
            repeat= False
            Channel_list=[]
            for row in range(NUM_BI_SLOTS):
                ch_name = self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_NAME_COL).text() 
                if (ch_name != "?"):
                    Channel_list.append(ch_name)
            
                    
            self.logger.info("Supervisor: Setting LV OFF for ch " +str(Channel_list))
            for channel in Channel_list:
                self.SendCAENControllerCmd("TurnOff,PowerSupplyId:caen,ChannelId:"+channel)
            
            time.sleep(30)
            
            for row in range(NUM_BI_SLOTS):
                ch_name = self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_NAME_COL).text() 
                if (ch_name != "?"):
                    if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_STAT_COL).text()!="OFF"):
                        repeat=True    
            
    
    def JULABO_safeTemp(self):
        if self.SharedDict["BI_Active"]: 
            self.BI_Abort()
        Sp_id = 0
        value = 20
        self.logger.info("Supervisor: Setting JULABO Sp"+str(Sp_id+1)+ " to " +str(value))
        
        self.Julabo.lock.acquire()
        while (self.SharedDict["Ctrl_Sp1"].text()!="20.00"):
            if not self.Julabo.is_connected :
                self.Julabo.connect()
            if self.Julabo.is_connected :
                try:
                    self.Julabo.sendTCP("out_sp_0"+str(Sp_id)+" "+str(value))
                    self.logger.info("Supervisor: JULABO cmd sent")                    
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
                
        while (self.SharedDict["Ctrl_TSp"].text()!="1"):    
            self.logger.info("Supervisor: Selecting JULABO Sp"+str(Sp_id+1))
            if not self.Julabo.is_connected :
                self.Julabo.connect()
            if self.Julabo.is_connected :
                try:
                    self.Julabo.sendTCP("out_mode_01 "+str(Sp_id))
                    self.logger.info("Supervisor: JULABO cmd sent")
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
            
        self.Julabo.lock.release()
            
            
            
    def BI_Completion_Alert(self):
        self.send_alert("BurnIn completed.")
            
            
    def BI_Abort(self):
        self.logger.info("SUPERVISOR: Requesting BI to be aborted")
        self.BI_Abort_sig.emit()
        count=10
        time.sleep(1)
        while (self.SharedDict["BI_Active"]):
            time.sleep(5)
            self.logger.info("SUPERVISOR: Waiting BI to be aborted")
            count-=1
            if (count==0):
                self.logger.warning("Supervisor: Could not abort BI test. Going ahead with my stuff...")
                break
            
        
    
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
        self.CAENController.lock.release()
