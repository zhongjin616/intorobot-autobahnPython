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

import time 
class EchoClientProtocol(WebSocketClientProtocol):

   def onConnect(self, response):
      pass
      #print(response)

   def sendDatastream(self):
      self.sendMessage(datastream)
      print "datastream send"
      
   def sendRobotInformation(self):
      self.sendMessage(robotDatastreamsInformation)
      self.sendMessage(robotCommandstreamsInformation)
      
   def onOpen(self):
      print "websocket established, sending robotinformation and datastream"
      self.sendRobotInformation()
      reactor.callLater(3, self.sendDatastream)
    
   def onClose(self):
       print "receive Close handshake from server" 

   def onMessage(self,payload,isBinary): 
      print str(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time())))  
      print "receive confirm message: ",payload


import os,base64,sys,binascii
class EchoClientVideoProtocol(WebSocketClientProtocol):
    
   def constructBinary(self): 
       data_in = os.urandom(1000) 
       encoded = json.dumps(base64.b64encode(data_in).decode('ascii')) 
       return encoded 

   def onConnect(self, response):
      pass
      #print(response)

   def sendVideostream(self):
      self.NUM = self.NUM + 1
      video = os.urandom(1000) 
      print "video size is ",len(video)
      self.sendMessage(video,True)
      logger.info( "video send. NUM: %d", self.NUM )
      if self.NUM < 200 :
          reactor.callLater(0.1, self.sendVideostream)
      
   def sendRobotInformation(self):
      self.sendMessage(robotDatastreamsInformation)
      self.sendMessage(robotCommandstreamsInformation)
      
   def onOpen(self): 
      self.NUM = 0 
      print "websocket established, sending robotinformation and datastream"
      #self.sendRobotInformation()
      reactor.callLater(2, self.sendVideostream)
      
   def onMessage(self,payload,isBinary):
      data = json.loads(payload)
      if data.has_key("commandstreams"):
        left_speed = data["commandstreams"][0]["current_value"]["value"]
        right_speed = data["commandstreams"][0]["current_value"]["value"]
        values = [left_speed, right_speed]
        print "receive command message: ",values
      else:
        print "receive confirm message: ",payload 
   
   
   def onClose(self,wasClean, code, reason):
        self.sendClose() 



import logging
import argparse
if __name__ == '__main__':
   
    parser = argparse.ArgumentParser() 
    parser.add_argument("-i","--ip",type=str,default="127.0.0.1",help="spcify listenning ip address.")
    parser.add_argument("-p","--port",type=str,default="9000",help="spcify listenning port.")
    parser.add_argument("-l","--loglevel",type=str,default="debug",help="spcify logging level")
    parser.add_argument("-n","--loggername",type=str,default="test-robot",help="logger name") 
    parser.add_argument("-f","--filename",type=str,default="test-robot.log",help="logger file name")

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
    factory=WebSocketClientFactory('ws://{}:{}/v1/websocket/?feed_id=53dde5e6a52633d704000003&format=json&isFront=False'.format(args.ip,args.port),
                                    debug = args.loglevel,
                                    debugCodePaths = False)
    factory.protocol = EchoClientProtocol
    
    
    #factoryVideo=WebSocketClientFactory('ws://162.243.154.223:8888/v1/websocket/feed_id=53dde5e6a52633d704000003&format=video&isFront=False',
    #factoryVideo=WebSocketClientFactory('ws://192.168.1.37:9000/v1/websocket/?feed_id=53dde5e6a52633d704000003&format=video&isFront=False',
    factoryVideo=WebSocketClientFactory('ws://{}:{}/v1/websocket/?feed_id=53dde5e6a52633d704000003&format=video&isFront=False'.format(args.ip,args.port),
                                    debug = args.loglevel,
                                    debugCodePaths = False)
    factoryVideo.protocol = EchoClientVideoProtocol
    # connectWS(factory)
    connectWS(factoryVideo)
    reactor.run()
