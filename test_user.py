###############################################################################
##
##  Copyright (C) 2013 molmc
##
##
###############################################################################

import sys
import json
import dbus
from twisted.internet import reactor
from twisted.python import log

from autobahn.twisted.websocket import WebSocketClientFactory, \
                                       WebSocketClientProtocol, \
                                       connectWS


commandstream = """{
"leftspeed": %d,  
"rightspeed": %d
}""".encode("UTF-8")


class EchoClientProtocol(WebSocketClientProtocol):

   def onConnect(self, response):
      self.leftspeed = 0
      self.rightspeed = 0
      #print(response)

   def sendCommandstream(self):
      self.leftspeed += 1
      self.rightspeed += 1
      string=commandstream%(self.leftspeed,self.rightspeed)
      self.sendMessage(string)
      print ("send speed:%d, %d to robot"%(self.leftspeed,self.rightspeed))
      reactor.callLater(2, self.sendCommandstream)
      
   def onOpen(self):
      print "websocket established, sending robotinformation and datastream"
      reactor.callLater(2, self.sendCommandstream)
      
   def onMessage(self,payload,isBinary):
      #print "receive datastream: ",payload 
      print payload 
      print "onMessage() receive jsonData from robot at: %s "%str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))

   def onClose(self,wasClean, code, reason):
       self.sendClose()  


import time
class EchoClientVideoProtocol(WebSocketClientProtocol):

   def onConnect(self, response):
      pass
      #print(response)
     
   def onOpen(self):
      self.NUM = 0 
      print "websocket established, wait for robot video..."

      
   def onMessage(self,payload,isBinary):
       self.NUM = self.NUM + 1 
       print "size of payload %d"%len(payload)
       logger.info( "receive video frame %d ",self.NUM )
       #print "onMessage() receive video from robot at: %s "%str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
   def onClose(self,wasClean, code, reason):
        self.sendClose() 



import logging
import argparse
if __name__ == '__main__':
   
    parser = argparse.ArgumentParser() 
    parser.add_argument("-i","--ip",type=str,default="127.0.0.1",help="spcify listenning ip address.")
    parser.add_argument("-p","--port",type=str,default="9000",help="spcify listenning port.")
    parser.add_argument("-l","--loglevel",type=str,default="debug",help="spcify logging level")
    parser.add_argument("-n","--loggername",type=str,default="test-user",help="logger name") 
    parser.add_argument("-f","--filename",type=str,default="test-user.log",help="logger file name")

    args = parser.parse_args() 
    if args.loglevel == "debug": 
        level = logging.DEBUG
    elif args.loglevel == "info": 
        level = logging.INFO
    elif args.loglevel == "warn": 
        level = logging.WARNING
    elif args.loglevel == "error": 
        level = logging.ERROR
    elif args.loglevel == "critical": 
        level = logging.CRITICAL

    logger = logging.getLogger(args.loggername) 
    logger.setLevel(logging.DEBUG) 
    fh = logging.FileHandler(args.filename) 
    fh.setLevel(level)
    ch = logging.StreamHandler() 
    ch.setLevel(level) 
    formatter = logging.Formatter('%(asctime)s-%(name)s:-%(levelname)s: %(message)s')
    fh.setFormatter(formatter) 
    ch.setFormatter(formatter) 
    logger.addHandler(fh) 
    logger.addHandler(ch)
   
    
    #factory=WebSocketClientFactory( 'ws://162.243.154.223:8888/v1/websocket/feed_id=53dde5e6a52633d704000003&format=json&isFront=False',
    #factory=WebSocketClientFactory( 'ws://192.168.1.37:9000/v1/websocket/?feed_id=53dde5e6a52633d704000003&format=json&isFront=False',
    factory=WebSocketClientFactory( 'ws://143.89.46.81:8888/v1/websocket/?feed_id=53dde5e6a52633d704000003&format=json&isFront=True',
                                    debug = args.loglevel,
                                    debugCodePaths = False)
    factory.protocol = EchoClientProtocol
    
    
    #factoryVideo=WebSocketClientFactory('ws://162.243.154.223:8888/v1/websocket/feed_id=53dde5e6a52633d704000003&format=video&isFront=False',
    #factoryVideo=WebSocketClientFactory('ws://192.168.1.37:9000/v1/websocket/?feed_id=53dde5e6a52633d704000003&format=video&isFront=False',
    factoryVideo=WebSocketClientFactory('ws://143.89.46.81:8888/v1/websocket/?feed_id=53dde5e6a52633d704000003&format=video&isFront=True',
                                    debug = args.loglevel,
                                    debugCodePaths = False)
    factoryVideo.protocol = EchoClientVideoProtocol
    # connectWS(factory)
    connectWS(factoryVideo)
    reactor.run()
