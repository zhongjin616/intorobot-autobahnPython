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
robotDatastreamsInformation = """{
    "method": "POST",
    "resource": "/feeds/53dde5e6a52633d704000003/datastreams",
    "headers": {"X-ApiKey" : "EMPTY"},
    "datastreams": [
        {
            "id": "d_temperature",
            "title": "temperature",
            "description": "indoor temperature",
            "type": "value",
            "attribute":
                {
                    "unit_name": "Degree",
                    "unit_symbol": "C",
                    "min_val": -50,
                    "max_val": 100
                }
        },
        {
            "id": "d_left_speed",
            "title": "left-speed",
            "description": "speed of Thymio left wheel",
            "type": "value",
            "attribute":
                {
                    "unit_name": "RoundPerMinuet",
                    "unit_symbol": "rpm",
                    "min_val": -500,
                    "max_val": 500
                }
        },
        {
            "id": "d_right_speed",
            "title": "right-speed",
            "description": "speed of Thymio right wheel",
            "type": "value",
            "attribute":
                {
                    "unit_name": "RoundPerMinuet",
                    "unit_symbol": "rpm",
                    "min_val": -500,
                    "max_val": 500
                }
        },
        {
            "id": "d_image",
            "title": "image",
            "description": "image taken by thymio",
            "type": "image",
            "attribute":
                {
                    "format": "image"
                }
        },
        {
            "id": "d_video",
            "title": "video",
            "description": "video come from thymio",
            "type": "video",
            "attribute":
                {
                    "format": "video"
                }
        }
    ],
    "token" : "0x12345"
}""".encode('UTF-8')


robotCommandstreamsInformation = """{
    "method": "POST",
    "resource": "/feeds/53dde5e6a52633d704000003/commandstreams",
    "headers": {"X-ApiKey" : "EMPTY"},
    "commandstreams": [
        {
            "id": "c_left_speed",
            "title": "left-speed",
            "description": "set left wheel speed",
            "type": "value",
            "attribute":
                {
                    "unit_name": "RoundPerMinuet",
                    "unit_symbol": "rpm",
                    "min_val": -500,
                    "max_val": 500
                }
        },
        {
            "id": "c_right_speed",
            "title": "right-speed",
            "description": "set right wheel speed",
            "type": "value",
            "attribute":
                {
                    "unit_name": "RoundPerMinuet",
                    "unit_symbol": "rpm",
                    "min_val": -500,
                    "max_val": 500
                }
        }
    ],
    "token" : "0x23456"
}""".encode('UTF-8')


datastream = """{
        "resource": "/feeds/53dde5e6a52633d704000003/datastreams",
        "datastreams": [
            {
                "id" : "d_left_speed",
                "current_value":
                {
                "timestamp": 1405555300,
                "value": 300
                }
            },
            {
                "id": "d_right_speed",
                "current_value" :
                {
                "timestamp": 1405555300,
                "value": 300
                }
            },
            {
                "id": "d_temperature",
                "current_value" :
                {
                "timestamp": 1405555300,
                "value": 30
                }
            }, 
            {
                "id": "d_image",
                "current_value" :
                {
                "timestamp": 1405555300,
                "value":30 
                }
            }
 
        ],
        "token": "0x34567"
    }""".encode('UTF-8') 

#deprecated 
videostream = """{
        "resource": "/feeds/53dde5e6a52633d704000003/datastreams",
        "datastreams": [
            {
                "id": "d_video",
                "current_value":
                {
                "timestamp": 1405555300,
                "value": 44444444444444444444444444445555555555555555555555555555555556666666666666666666666666666666
                }
            },
            {
                "id": "d_image",
                "current_value":
                {
                "timestamp": 1405555300,
                "value": 111111111111111111111111111122222222222222222222222222222233333333333333333333333333333333333
                }
            }
        ],
        "token": "0x76589"
    }""".encode('UTF-8')

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
      
   def onMessage(self,payload,isBinary):
      data = json.loads(payload)
      if data.has_key("commandstreams"):
        left_speed = data["commandstreams"][0]["current_value"]["value"]
        right_speed = data["commandstreams"][0]["current_value"]["value"]
        values = [left_speed, right_speed]
        print "receive command message: ",values
      else:
        print "receive confirm message: ",payload

class EchoClientVideoProtocol(WebSocketClientProtocol):

   def onConnect(self, response):
      pass
      #print(response)

   def sendVideostream(self): 
      video = b"hello,wolrd!123"
      #video = 0x1234567890
      self.sendMessage(video,True)
      print "video send!"
      
   def sendRobotInformation(self):
      self.sendMessage(robotDatastreamsInformation)
      self.sendMessage(robotCommandstreamsInformation)
      
   def onOpen(self):
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





if __name__ == '__main__':
   
    debug = True
    
    #factory=WebSocketClientFactory( 'ws://162.243.154.223:8888/v1/websocket/feed_id=53dde5e6a52633d704000003&format=json&isFront=False',
    factory=WebSocketClientFactory( 'ws://192.168.1.37:9000/v1/websocket/?feed_id=53dde5e6a52633d704000003&format=json&isFront=False',
                                    debug = debug,
                                    debugCodePaths = debug)
    factory.protocol = EchoClientProtocol
    
    
    #factoryVideo=WebSocketClientFactory('ws://162.243.154.223:8888/v1/websocket/feed_id=53dde5e6a52633d704000003&format=video&isFront=False',
    factoryVideo=WebSocketClientFactory('ws://192.168.1.37:9000/v1/websocket/?feed_id=53dde5e6a52633d704000003&format=video&isFront=False',
                                    debug = debug,
                                    debugCodePaths = debug)
    factoryVideo.protocol = EchoClientVideoProtocol
    connectWS(factory)
    connectWS(factoryVideo)
    reactor.run()
