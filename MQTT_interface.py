

import sys, time
from paho.mqtt import client as mqtt_client
from datetime import datetime

class MQTT_interface():

	def __init__(self,configDict,logger, clientId):
	
		super(MQTT_interface,self).__init__();
		self.is_connected = False
		self.is_subscribed = False
		
		self.LastSource = "None"
		
		self.LastCAENMessageTS = "NEVER"
		self.LastCAENMessage = ""
		
		self.LastM5MessageTS = "NEVER"
		self.LastM5Message = ""
		
		self.ClientId=clientId
		
		
		self.configDict=configDict
		self.logger = logger
		self.Addr = configDict.get(("MQTT","Addr"),"NOKEY")
		if self.Addr == "NOKEY":
			self.Addr = "192.168.0.45"
			self.logger.warning("MQTT addr parameter not found. Using default")
		self.Port = configDict.get(("MQTT","Port"),"NOKEY")
		if self.Port == "NOKEY":
			self.Port = "1883"
			self.logger.warning("MQTT port parameter not found. Using default")
		self.CAENTopic = configDict.get(("MQTT","CAENTopic"),"NOKEY")
		if self.CAENTopic == "NOKEY":
			self.CAENTopic = "/caenstatus/full"
			self.logger.warning("MQTT CAENTopic parameter not found. Using default")
		self.M5Topic = configDict.get(("MQTT","M5Topic"),"NOKEY")
		if self.M5Topic == "NOKEY":
			self.M5Topic = "/caenstatus/full"
			self.logger.warning("MQTT M5Topic parameter not found. Using default")
		try:	
			self.client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1,self.ClientId)
		except Exception as e:
			self.logger.warning("MQTT client: client creation failed. Assuming MQTT version <2.0.")
			self.client = mqtt_client.Client(self.ClientId)
			
		self.client.on_connect = self.on_connect
		self.client.on_message = self.on_message
		self.client.on_disconnect = self.on_disconnect
		self.client.on_publish = self.on_publish
		self.logger.info("MQTT class initialized")
	
	def on_connect(self,client, userdata, flags, rc):  #create function for callback
		self.logger.info("MQTT client: Connected to MQTT Broker!")
		self.client.subscribe(self.CAENTopic)
		self.client.subscribe(self.M5Topic)
		self.is_connected = True
		
	def on_disconnect(self, client, userdata, rc):  #create function for callback
		if rc != 0:
			self.logger.info("MQTT client: DISConnected to MQTT Broker!")
			self.is_connected = False
			
	def on_message(self, client, userdata, msg):  #create function for callback
		try:
			self.logger.debug(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
			self.LastSource = msg.topic
			if self.LastSource == "/caenstatus/full":
				self.LastCAENMessage = msg.payload.decode()	
				self.LastCAENMessageDT = datetime.now()	
				self.LastCAENMessageTS = self.LastCAENMessageDT.strftime("%d/%m/%Y %H:%M:%S")
			elif self.LastSource == "/environment/HumAndTemp001":
				self.LastM5Message = msg.payload.decode()	
				self.LastM5MessageDT = datetime.now()	
				self.LastM5MessageTS = self.LastM5MessageDT.strftime("%d/%m/%Y %H:%M:%S")
			else:
				self.logger.warning("MQTT client: Message from unknown topic")
		except Exception as e:
			self.logger.info("MQTT client: invalid string from MQTT Broker!")
	
	def on_publish(self,client,userdata,result):             #create function for callback
    		pass
    	
	def publish(self, topic, msg):
		pub_result = self.client.publish(topic,msg,0,True)
		if pub_result[0] != 0:
  			self.logger.error("MQTT client: Failed to publish message on topic "+topic)
		
	def connect(self):
		
		try:
			self.client.connect(self.Addr, int(self.Port))
			self.is_subscribed = True
			self.client.loop_start()
			return True
		except Exception as e: 
			self.logger.error(e)
			return False
		
		
		
		
		
