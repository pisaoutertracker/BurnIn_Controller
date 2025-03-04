import requests

class DB_interface():

	def __init__(self,configDict,logger):
	
		super(DB_interface,self).__init__();
		
		self.configDict=configDict
		self.logger = logger
		
		self.Addr = configDict.get(("DB","Addr"),"NOKEY")
		if self.Addr == "NOKEY":
			self.Addr = "192.168.0.45"
			self.logger.warning("DB addr parameter not found. Using default")
		self.Port = configDict.get(("DB","Port"),"NOKEY")
		
		self.ClientId = "BurnIn_Controller"
		

		self.logger.info("DB interface class initialized")
	
	def uploadSessionToDB(self,sessionDescription = {}):
	
		self.logger.info(sessionDescription)
		# URL of the API endpoint
		api_url = "http://%s:%d/sessions"%(self.Addr, int(self.Port))
		
		# Send a PUT request
		try:
			response = requests.post(api_url, json=sessionDescription,timeout=5)
		except requests.exceptions.Timeout:
			return "timeout"
		except requests.exceptions.RequestException as e:
			raise SystemExit(e)
	
		# Check the response
		if response.status_code == 201:
			self.logger.info("Session \"%s\" created successfully"%response.json()["sessionName"])
			self.logger.info(response.text)
		else:
			self.logger.error("Failed to update the session. Status code:", response.status_code)
		return response.json()["sessionName"]
		
		### read the test result from DB

	def getSessionFromDB(self,sessionName):
		self.logger.info("Calling getTestFromDB() %s", sessionName)
		api_url = "http://%s:%d/sessions/%s"%(self.Addr, int(self.Port), sessionName)
		response = requests.get(api_url)
		if response.status_code == 200:
			self.logger.info("Session successfully pulled.")
		else:
			self.logger.error("Failed to pull the session. Status code:%d", response.status_code)
		return eval(response.content.decode())
		
	def getConnectionsFromDB(self,LVNames,HVNames,fc7IDs,fc7Slots):
		self.logger.info("Getting connection from DB")
		api_url = "http://%s:%d/snapshot"%(self.Addr, int(self.Port))
		print(api_url)
		for slot in range(0,10):
			slotName = "B"+str(slot+1)
			snapshot_data = { "cable": slotName, "side": "crateSide"}
			response = requests.post(api_url, json=snapshot_data)
			if response.status_code == 200:
				self.logger.info("Slot "+ str(slot+1)+ " connections successfully pulled.")
				jsonResponse=response.json()
				self.logger.debug (jsonResponse)
				if slot==0:
					self.logger.info (jsonResponse)
				for val in jsonResponse["4"]["connections"]:
					if val["cable"][0:5]=="XSLOT":
					        LVNames[slot] = "LV%s_%d"%(str.lower(val["cable"][5:]),int(val["line"]))
				for val in jsonResponse["3"]["connections"]:
					if val["cable"][0:5]=="ASLOT":
					        HVNames[slot] = "HV%s_%d"%(str.lower(val["cable"][5:]),int(val["line"]))
				for val in jsonResponse["1"]["connections"]:
					if val["cable"][0:3]=="FC7":
						fc7IDs[slot] = str.lower(val["cable"])
						fc7Slots[slot] = str.lower(val["det_port"][0][2:])
					        #
			else:
				self.logger.error("Slot "+ str(slot+1)+ " connections pull failed. Status code:%d", response.status_code)
		return
		
	def uploadModuleNameToDB(self,slot,ID):
		self.logger.info("Loading new module connections to DB")
		reqSlotName = "B"+str(slot+1)
		
		#check if module exists and if it is connected to something
		self.logger.info("Checking module status in DB")
		snapshot_data = { "cable": ID, "side": "crateSide"}
		api_url = "http://%s:%d/snapshot"%(self.Addr, int(self.Port))
		response = requests.post(api_url, json=snapshot_data)
		if response.status_code == 200:
			self.logger.info("Module "+ ID+ " connections successfully pulled.")
			jsonResponse=response.json()
			self.logger.debug (jsonResponse)
			connections = jsonResponse["1"]["connections"]
			if len(connections):
				connSlot=connections[0]["cable"]
				self.logger.info("Module "+ ID+ " is already connected to slot "+connSlot)
				if connSlot==reqSlotName:
					self.logger.info("Module "+ ID+ " already connected to slot "+connSlot)
					return
				else:
					self.disconnectModuleSlot(ID,connSlot)
				
		else:
			self.logger.error("Slot "+ str(slot+1)+ " status check failed. Status code:%d", response.status_code)
			return


		#check if requested slot exists and if it is connected to something			
		self.logger.info("Checking slot status in DB")
		snapshot_data = { "cable": reqSlotName, "side": "detSide"}
		api_url = "http://%s:%d/snapshot"%(self.Addr, int(self.Port))
		response = requests.post(api_url, json=snapshot_data)
		if response.status_code == 200:
			self.logger.info("Slot "+ reqSlotName+ " connections successfully pulled.")
			jsonResponse=response.json()
			self.logger.debug (jsonResponse)
			connections = jsonResponse["1"]["connections"]
			if len(connections):
				connID=connections[0]["cable"]
				self.logger.info("Slot "+ reqSlotName+ " is already connected to module "+connID)
				if connID==ID:
					self.logger.info("Module "+ ID+ " already connected to slot "+connSlot)
					return
				else:
					self.disconnectModuleSlot(connID,reqSlotName)
		else:
			self.logger.error("Slot "+ str(slot+1)+ " status check failed. Status code:%d", response.status_code)
			return	

		self.connectModuleSlot(ID,reqSlotName)	
		return


	def disconnectModuleSlot(self,ID,connSlot):
		self.logger.info("Disconnecting module "+ID+" from slot "+connSlot)
		api_url = "http://%s:%d/disconnect"%(self.Addr, int(self.Port))
		data_power = {
			"cable1": ID,
			"cable2": connSlot,
			"port1": "power",
			"port2": "power"
		}
		data_fiber = {
			"cable1": ID,
			"cable2": connSlot,
			"port1": "fiber",
			"port2": "fiber"
		}			
		response = requests.post(api_url, json=data_power)
		if response.status_code == 200:
			self.logger.info("Module "+ ID+ " power connection removed.")
			jsonResponse=response.json()
			self.logger.debug (jsonResponse)
		else:
			self.logger.error("Module "+ ID+ " power connection removal failed. Status code:%d", response.status_code)
		response = requests.post(api_url, json=data_fiber)
		if response.status_code == 200:
			self.logger.info("Module "+ ID+ " fiber connection removed.")
			jsonResponse=response.json()
			self.logger.debug (jsonResponse)
		else:
			self.logger.error("Module "+ ID+ " fiber connection removal failed. Status code:%d", response.status_code)
	
	
	def connectModuleSlot(self,ID,connSlot):
		self.logger.info("connecting module "+ID+" from slot "+connSlot)
		api_url = "http://%s:%d/connect"%(self.Addr, int(self.Port))
		data_power = {
			"cable1": ID,
			"cable2": connSlot,
			"port1": "power",
			"port2": "power"
		}
		data_fiber = {
			"cable1": ID,
			"cable2": connSlot,
			"port1": "fiber",
			"port2": "fiber"
		}			
		response = requests.post(api_url, json=data_power)
		if response.status_code == 200:
			self.logger.info("Module "+ ID+ " power connection added.")
			jsonResponse=response.json()
			self.logger.debug (jsonResponse)
		else:
			self.logger.error("Module "+ ID+ " power connection failed. Status code:%d", response.status_code)
		response = requests.post(api_url, json=data_fiber)
		if response.status_code == 200:
			self.logger.info("Module "+ ID+ " fiber connection added.")
			jsonResponse=response.json()
			self.logger.debug (jsonResponse)
		else:
			self.logger.error("Module "+ ID+ " fiber connection failed. Status code:%d", response.status_code)
	
	
	def StartSesh(self,session_dict):
		self.logger.info("Database session uploading. Please wait...")
                
		#define test session for DB
		session = {
			"operator": session_dict["Operator"],
			"timestamp": session_dict["Timestamp"],
			"testType": session_dict["TestType"],
			"description": session_dict["Description"], 
			"temperatures": {
				"low": session_dict["LowTemp"],
				"high": session_dict["HighTemp"],
				},
			"underRamp": session_dict["UnderRamp"], 
			"underKeep": session_dict["UnderKeep"], 
			"nCycles": session_dict["NCycles"],
			"test": session_dict["NCycles"],
			"modulesList": [],
			"stepList": session_dict["StepList"]
		}

                #omit disabled modules
		for idx,ActiveSlot in enumerate(session_dict["ActiveSlots"]):
			if not ActiveSlot:
				session["modulesList"].append("")
			else:
				session["modulesList"].append(session_dict["ModuleIDs"][idx]),
        
                #send session to MongoDB here
		uploadResponse=self.uploadSessionToDB(session)
                #(make sure the Session ID doesn't already exist)
                #now get it back to display
		if uploadResponse=="timeout": #if it times out, display a dummy status
			session_fromDB=session
			self.TestSession=uploadResponse
			session_dict["Session"]=self.TestSession
			self.logger.error("DATABASE	: Session loading timed out!")
		else:
			session_fromDB=self.getSessionFromDB(uploadResponse)#default for testing
			self.TestSession=session_fromDB["sessionName"]
			session_dict["Session"]=self.TestSession
			self.logger.info("DATABASE: Session loaded!")
			with open('./lastSession.txt', 'w') as f:
				f.write(str(self.TestSession))
