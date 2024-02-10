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
		if self.Port == "NOKEY":
			self.Port = "5000"
			self.logger.warning("MQTT port parameter not found. Using default")
		self.ClientId = configDict.get(("MQTT","ClientId"),"NOKEY")
		

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

	def getSessionFromDB(sessionName):
		self.logger.info("Calling getTestFromDB() %s", sessionName)
		api_url = "http://%s:%d/sessions/%s"%(self.Addr, int(self.Port), sessionName)
		response = requests.get(api_url)
		if response.status_code == 200:
			self.logger.info("Session successfully pulled.")
		else:
			self.logger.error("Failed to pull the session. Status code:%d", response.status_code)
		return eval(response.content.decode())

	def StartSesh(self,session_dict):
		self.logger.info("Database session uploading. Please wait...")
                
		#define test session for DB
		session = {
			"operator": session_dict["Operator"],
			"timestamp": session_dict["Timestamp"],
                	"description": session_dict["Description"], 
			"temperatures": {
				"low": session_dict["LowTemp"],
        			"high": session_dict["HighTemp"],
                	},                        
#			"configuration": [""]*10,
			"modulesList": [],
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
			session_fromDB=self.getSessionFromDB(sessionName=uploadResponse)#default for testing
			self.TestSession=session_fromDB["sessionName"]
			session_dict["Session"]=self.TestSession
			self.logger.info("DATABASE: Session loaded!")
			pprint(session_fromDB)