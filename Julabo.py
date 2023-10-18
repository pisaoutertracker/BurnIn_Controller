
import sys
import socket
import argparse
import time
from select import select

class Julabo():

	def __init__(self): 
		super(Julabo, self).__init__()
		self.connected=0           
		self.interfaces = []

	def connect(self,tcpIP,tcpPORT):
			
		if self.connected==1:
			sys.stdwar.write("device already connected\n")
		else:
			try:
				sys.stdout.write("Connecting to device..."+"\n")
				self.TCPSock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
				self.TCPSock.connect((tcpIP,tcpPORT))           
				self.interfaces.Append(self.TCPSock)       # [self.UDPSock,self.TCPSock]
				self.connected = 1
				
			except socket.error as e:
				sys.stderr.write("Device connection error:"+str(e)+"\n")        
				self.connected=0
				
	def close(self):
		if self.connected==0:
			sys.stderr.write("No connection to be closed\n")  
			return
		self.TCPSock.close()
		self.connected=0
					
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
		if self.connected==1:
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
	if Chiller.connected==1:
		print ("Attempting to send command: " + args.cmd)
		Chiller.sendTCP(str(args.cmd))
		print(Chiller.receive())
		Chiller.close()
		
  
if __name__=="__main__": 
    main() 
		
		
		
		
		
		
		
		
		
		
		
		
		