
import sys
import socket
import argparse
import time
from threading import Lock

from select import select

class BurnIn_TCP():

    def __init__(self,configDict,logger, moduleName): 
        super(BurnIn_TCP, self).__init__()
        self.is_connected=False 
        self.lock = Lock()    
        self.interfaces = []
        self.moduleName = moduleName
        self.configDict=configDict
        self.logger = logger
        self.Addr = configDict.get((self.moduleName,"Addr"),"NOKEY")
        if self.Addr == "NOKEY":
            self.Addr = "169.254.218.204"
            self.logger.warning(self.moduleName + " addr parameter not found. Using default")
        self.Port = configDict.get((self.moduleName,"Port"),"NOKEY")
        if self.Port == "NOKEY":
            self.Port = "5050"
            self.logger.warning(self.moduleName + " port parameter not found. Using default")
        

    def connect(self):
            
        if self.is_connected:
            self.logger.warning(self.moduleName + ": device already connected\n")
        else:
            try:
                self.logger.info(self.moduleName + ": Connecting to device...")
                self.TCPSock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                self.TCPSock.connect((self.Addr,int(self.Port))) 
                self.interfaces.clear()
                self.interfaces.append(self.TCPSock)       # [self.UDPSock,self.TCPSock]
                self.is_connected = True
                self.logger.info(self.moduleName + ": Connected!")
                
            except socket.error as e:
                self.logger.error(self.moduleName + ": Device connection error:"+str(e))        
                self.is_connected = False
                
    def close(self):
        if not self.is_connected:
            self.logger.warning(self.moduleName + ": No connection to be closed")  
            return
        self.TCPSock.close()
        self.is_connected = False
                    
    def receive(self):
        max_iter = 2
        reply = ""
        while (max_iter > 0):
            inputReady,outputReady,exceptReady = select(self.interfaces,[],[],1)  #wait for data in interfaces list
            time.sleep(0.020)
            for s in inputReady:              
                if s == self.TCPSock:
                    try:
                        self.buffer = self.readTCP(2048).decode()
                        self.logger.debug(self.moduleName + " stream received: "+self.buffer)
                        if self.moduleName == "Julabo":
                            return self.buffer[:-2]
                        elif self.moduleName == "CAENController":
                            return self.buffer[8:]
                        elif self.moduleName == "FNALBox":
                            reply= reply + self.buffer
                            if reply[-1:]=="]":
                                return reply
                            else:
                                self.logger.debug(self.moduleName + ": partial reply ending with :"+reply[-2:] +". trying to catch the rest.") 
                                max_iter-=1
                        else:
                            return self.buffer
                    except Exception as e:
                        self.logger.error(e)
                        self.is_connected = False
                else:
                    self.logger.error(self.moduleName + ": UNKNOWN SOCKET TYPE")
                    return "TCP error" 
            if self.moduleName == "CAENController" or self.moduleName == "Julabo": 
                self.logger.warning(self.moduleName + ": no reply")
                return "None"   
        self.logger.warning(self.moduleName + ": no or incomplete reply")
        return "None"   
        
    def sendTCP(self,message):
        if self.is_connected:
            try:
                if self.moduleName == "Julabo":
                    message = message+"\r"
                    self.TCPSock.send(message.encode())
                elif self.moduleName == "CAENController":
                    pknumber=0
                    messageLength = len(message) + 8
                    message = (messageLength).to_bytes(4, byteorder='big') +  (pknumber).to_bytes(4, byteorder='big')  + message.encode('utf-8')
                    self.TCPSock.send(message)
                else:    
                    self.TCPSock.send(message.encode())
                time.sleep(0.250) #as per JULABO datasheet
            except Exception as e:
                self.logger.error(self.moduleName + ": TCP send cmd failed")
                self.logger.error(e)
                self.is_connected = False
        else:
            self.logger.error(self.moduleName + ": can't send command, No device connected!")
        
    def readTCP(self,nByte = 20, peek = False):
        data,ip = self.TCPSock.recvfrom(nByte,peek * socket.MSG_PEEK)
        time.sleep(0.010) #as per JULABO datasheet
        return data

