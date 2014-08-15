#############################################################################
##
##  Copyright (C) 2013 molmc
##
##
###############################################################################

import sys
import tty 
import termios
import select 
import json
from twisted.internet import reactor
from twisted.python import log

from autobahn.twisted.websocket import WebSocketClientFactory, \
                                       WebSocketClientProtocol, \
                                       connectWS
moveBindings = {
        'i':(250,250),
        'j':(-250,250),
        'l':(250,-250),
        ',':(-250,-250),
        'k':(0,0),
}

def getKey():
        tty.setraw(sys.stdin.fileno())
        select.select([sys.stdin], [], [], 0)
        key = sys.stdin.read(1)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        return key

commandstream = """{
	"resource" :"/feeds/53dde5e6a52633d704000003/commandstreams",
	"commandstreams" : [
		{
			"id" : "c_left_speed",
			"current_value" :
			{
				"timestamp" : 1405555277,
				"value" : %d
			}
		},
		{
			"id" : "c_right_speed",
			"current_value" :
		{
			"timestamp" : 1405555277,
			"value" : %d
		}
		}
	],
	"token" : "0x98721"
}""".encode("UTF-8")


class EchoClientProtocol(WebSocketClientProtocol):

   def onConnect(self, response):
   	  self.leftspeed = 0
   	  self.rightspeed = 0
      #print(response)

   def sendCommandstream(self):
   	  #self.leftspeed += 10
   	  #self.rightspeed += 10
	  key = getKey()
          if key in moveBindings.keys():
               self.leftspeed = moveBindings[key][0]
               self.rightspeed = moveBindings[key][1]
          else: 
	       self.leftspeed = 0
	       self.rightspeed = 0
 	       
          string=commandstream%(self.leftspeed,self.rightspeed)
   	  self.sendMessage(string)
   	  print "send speed:%d, %d to robot"%(self.leftspeed,self.rightspeed)
   	  reactor.callLater(0.1, self.sendCommandstream)

   def onOpen(self):
      print "websocket established, sending robotinformation and datastream"
      reactor.callLater(0.1, self.sendCommandstream)
      
   def onMessage(self,payload,isBinary):
      print "receive datastream: ",payload 

   def onClose(self,wasClean, code, reason):
       self.sendClose()  


if __name__ == '__main__':

   debug = True 
   settings = termios.tcgetattr(sys.stdin) 

   #factory =  WebSocketClientFactory('ws://192.168.1.37:9000/v1/websocket/?feed_id=53dde5e6a52633d704000003&format=json&isFront=True',
   #factory =  WebSocketClientFactory('ws://162.243.154.223:9000/v1/websocket/?feed_id=53dde5e6a52633d704000003&format=json&isFront=True',
   factory =  WebSocketClientFactory('ws://143.89.46.81:8888/v1/websocket/?feed_id=53dde5e6a52633d704000003&format=json&isFront=True',
                                    debug = debug,
                                    debugCodePaths = debug)

   factory.protocol = EchoClientProtocol
   connectWS(factory)

   reactor.run()
