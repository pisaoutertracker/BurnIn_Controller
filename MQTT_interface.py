

import sys, time
from paho.mqtt import client as mqtt_client

class MQTT_interface():

	def __init__(self,configDict,logger):
	
		super(MQTT_interface,self).__init__();
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
		self.logger.info("MQTT class initialized")
		
	def connect(self):
		#self.client.connect(self.Addr, int(self.Port))
		time.sleep(10)