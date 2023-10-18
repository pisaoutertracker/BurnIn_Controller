
import sys
import socket
import argparse
import time
from select import select

class Julabo():

	def __init__(self,configDict,logger): 
		super(Julabo, self).__init__()
		self.is_connected=False           
		self.interfaces = []
		
		self.configDict=configDict
		self.logger = logger
		self.Addr = configDict.get(("Julabo","Addr"),"NOKEY")
		if self.Addr == "NOKEY":
			self.Addr = "169.254.218.204"
			self.logger.warning("Julabo addr parameter not found. Using default")
		self.Port = configDict.get(("Julabo","Port"),"NOKEY")
		if self.Port == "NOKEY":
			self.Port = "5050"
			self.logger.warning("Julabo port parameter not found. Using default")
		

	def connect(self):
			
		if self.is_connected:
			sys.stdwar.write("device already connected\n")
		else:
			try:
				sys.stdout.write("Connecting to JULABO device..."+"\n")
				self.TCPSock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
				self.TCPSock.connect((self.Addr,int(self.Port)))           
				self.interfaces.Append(self.TCPSock)       # [self.UDPSock,self.TCPSock]
				self.is_connected = True
				
			except socket.error as e:
				sys.stderr.write("Device connection error:"+str(e)+"\n")        
				self.is_connected = False
				
	def close(self):
		if not self.is_connected:
			sys.stderr.write("No connection to be closed\n")  
			return
		self.TCPSock.close()
		self.is_connected = False
					
	def receive(self):
		inputReady,outputReady,exceptReady = select(self.interfaces,[],[],1)  #wait for data in interfaces list
		for s in inputReady:              
			if s == self.TCPSock:        
				self.buffer = self.readTCP(2048)
				return self.buffer
			else:
				sys.stderr.write("UNKNOWN SOCKET TYPE")
				return "TCP error"
		return "None"   
		
	def sendTCP(self,message):
		if self.is_connected:
			self.TCPSock.send(message+"\r")
			time.sleep(0.250) #as per datasheet
		else:
			sys.stderr.write("No device connected!")
		
	def readTCP(self,nByte = 20, peek = False):
		data,ip = self.TCPSock.recvfrom(nByte,peek * socket.MSG_PEEK)
		time.sleep(0.010) #as per datasheet
		return data
		
		
	# Defining main function 
def main(): 

	parser = argparse.ArgumentParser()
	parser.add_argument('cmd', help="Please provide test cmd to be sent. i.e. \"status\"")
	args=parser.parse_args()
	
	print("Starting JULABO comm test...")
	Chiller = Julabo()
	Chiller.connect("169.254.218.204",5050)
	if Chiller.is_connected:
		print ("Attempting to send command: " + args.cmd)
		Chiller.sendTCP(str(args.cmd))
		print(Chiller.receive())
		Chiller.close()
		
  
if __name__=="__main__": 
    main() 
		
		
		
		
		
		
		
		
		
		
		
		
		