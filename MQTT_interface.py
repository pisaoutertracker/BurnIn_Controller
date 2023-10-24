

import sys, time
from paho.mqtt import client as mqtt_client
from datetime import datetime

class MQTT_interface():

	def __init__(self,configDict,logger):
	
		super(MQTT_interface,self).__init__();
		self.is_connected = False
		self.is_subscribed = False
		
		self.LastMessage = ""
		self.LastSource = "None"
		self.LastMessageTS = "NEVER"
		
		
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
		self.ClientId = configDict.get(("MQTT","ClientId"),"NOKEY")
		if self.ClientId == "NOKEY":
			self.ClientId = "BurnIn_Controller"
			self.logger.warning("MQTT ClientId parameter not found. Using default")
		self.CAENTopic = configDict.get(("MQTT","CAENTopic"),"NOKEY")
		if self.CAENTopic == "NOKEY":
			self.CAENTopic = "/caenstatus/full"
			self.logger.warning("MQTT CAENTopic parameter not found. Using default")
			
		self.client = mqtt_client.Client(self.ClientId)
		self.client.on_connect = self.on_connect
		self.client.on_message = self.on_message
		self.client.on_disconnect = self.on_disconnect
		self.logger.info("MQTT class initialized")
	
	def on_connect(self,client, userdata, flags, rc):
		self.logger.info("MQTT client: Connected to MQTT Broker!")
		self.client.subscribe(self.CAENTopic)
		self.is_connected = True
		
	def on_disconnect(self, client, userdata, rc):
		if rc != 0:
			self.logger.info("MQTT client: DISConnected to MQTT Broker!")
			self.is_connected = False
			
	def on_message(self, client, userdata, msg):
		try:
			self.logger.info(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
			self.LastMessage = msg.payload.decode()
			self.LastSource = msg.topic
			self.LastMessageTS = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
		except Exception as e:
			self.logger.info("MQTT client: invalid string from MQTT Broker!")
		
	def connect(self):
		
		try:
			self.client.connect(self.Addr, int(self.Port))
			self.is_subscribed = True
			self.client.loop_start()
			return True
		except Exception as e: 
			self.logger.error(e)
			return False
		
		
		
		
		