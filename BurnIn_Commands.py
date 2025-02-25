def addStep(self,action):
    self.logger.info("BI: cycle "+str(session_dict["Cycle"]) + " of "+str(NCycles))
    self.SharedDict["BI_Step"].setText(str(session_dict["CycleStep"])+" of "+str(len(session_dict["StepList"])))
    #
    if (action.upper()=="COOL"):
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
    #
    if (action.upper()=="HEAT"):
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
    #					
    if ( ["FULLTEST","CHECKID","QUICKTEST","DRYTEST"].includes(action.upper())):
	self.BI_Update_Status_file(session_dict)
	self.logger.info("BI: testing...")
	self.SharedDict["BI_Action"].setText(session_dict["Action"]+"  Module test")
	self.SharedDict["BI_TestActive"]=True
	session_dict["TestType"]=action
	for slot in Slot_list:
	    session_dict["fc7ID"]=self.SharedDict["BI_fc7IDs"][slot]
	    session_dict["fc7Slot"]=self.SharedDict["BI_fc7Slots"][slot]
	    session_dict["Current_ModuleID"]	= self.SharedDict["BI_ModuleIDs"][slot]
	    self.SharedDict["BI_SUT"].setText(str(slot+1)) 
	    self.logger.info("BI: testing BI slot "+str(slot)+": module name "+session_dict["Current_ModuleID"]+", fc7 slot "+session_dict["fc7Slot"]+",board "+session_dict["fc7ID"])
	    if not self.BI_Action(self.BI_StartTest_Cmd,False,session_dict):
		return
	self.SharedDict["BI_TestActive"]=False
	session_dict["TestType"]="Undef"
    #
    if (action.upper()=="SCANIV"):
	self.BI_Update_Status_file(session_dict)
	self.logger.info("BI: IV scan...")
	self.SharedDict["BI_Action"].setText("IV scan")
	self.SharedDict["BI_TestActive"]=True
	for slot in Slot_list:
	    session_dict["Current_ModuleID"]	= self.SharedDict["BI_ModuleIDs"][slot]
	    session_dict["Current_ModuleHV"]    = HV_Channel_list[slot]
	    self.SharedDict["BI_SUT"].setText(str(slot+1)) 
	    self.logger.info("BI: IV scan for slot "+str(slot)+": module name "+session_dict["Current_ModuleID"])
	    if not self.BI_Action(self.BI_StartIV_Cmd,False,session_dict):
		return
	self.SharedDict["BI_TestActive"]=False
    #
    if (action.upper()=="LV_ON"):
	self.BI_Update_Status_file(session_dict)
	self.logger.info("BI: Starting LVs")
	self.SharedDict["BI_Action"].setText("Starting LVs")
	self.SharedDict["BI_SUT"].setText("None") 
	if not self.BI_Action(self.Ctrl_PowerLV_Cmd,True,True,LV_Channel_list,PopUp):
	    return
        time.sleep(BI_SLEEP_AFTER_LVSET)
	#check all LVs are ON
	for row in Slot_list:
	    if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_STAT_COL).text()!="ON"):
		self.BI_Abort("BI aborted: some LVs was not turned ON")
		return
    #
    if (action.upper()=="LV_OFF"):
	self.BI_Update_Status_file(session_dict)
        self.logger.info("BI: Stopping LVs")
        self.SharedDict["BI_Action"].setText("Stopping LVs")
	self.SharedDict["BI_SUT"].setText("None") 
	if not self.BI_Action(self.Ctrl_PowerLV_Cmd,True,False,LV_Channel_list,PopUp):
	    return
	time.sleep(BI_SLEEP_AFTER_LVSET)
	#check all LVs are OFF
	for row in Slot_list:
	    if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_LV_STAT_COL).text()!="OFF"):
		self.BI_Abort("BI aborted: some LVs was not turned OFF")
		return
    #
    if (action.upper()=="HV_ON"):
	self.BI_Update_Status_file(session_dict)
	self.logger.info("BI: Starting HVs")
        self.SharedDict["BI_Action"].setText("Starting HVs")
	self.SharedDict["BI_SUT"].setText("None") 
	if not self.BI_Action(self.Ctrl_PowerHV_Cmd,True,True,HV_Channel_list,PopUp):
	    return
	time.sleep(BI_SLEEP_AFTER_HVSET)
	#check all HVs are ON
	for row in Slot_list:
	    if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_STAT_COL).text()!="ON"):
		self.BI_Abort("BI aborted: some HVs was not turned ON")
		return
				
    #							
    if (action.upper()=="HV_OFF"):
	self.BI_Update_Status_file(session_dict)
	self.logger.info("BI: Stopping HVs")
	self.SharedDict["BI_Action"].setText("Stopping HVs")
	self.SharedDict["BI_SUT"].setText("None") 
	if not self.BI_Action(self.Ctrl_PowerHV_Cmd,True,False,HV_Channel_list,PopUp):
	    return
	time.sleep(BI_SLEEP_AFTER_HVSET)
	#check all HVs are OFF
	for row in Slot_list:
	    if(self.SharedDict["CAEN_table"].item(row,CTRLTABLE_HV_STAT_COL).text()!="OFF"):
		self.BI_Abort("BI aborted: some LVs was not turned OFF")
		return
				
					
