#!/usr/bin/env python

#################################################### 
#                                                  # 
#                                                  #
#       INTOROBOT PLATFORM                         #
#       AUTOBAHN SERVER                            #
#                                                  #
#################################################### 

from autobahnDB import * #interface of postgreSQL 
from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketServerFactory,\
        WebSocketServerProtocol,\
        listenWS

###To get access to Postgre database

db = autobahnDB("exampledb",host="localhost",user="dbuser",passwd="dbuser") 

#db = autobahnDB("molmcdb",host="localhost",user="postgres",passwd="123") 

import time
import json 
import logging 


###define custom protocol to handle websocket data 

class IntorobotServerProtocol(WebSocketServerProtocol): 
    def onConnect(self,request):
        logger.debug(request)
        params = request.params
        if params.has_key("feed_id"): 
            self.feed_id = params["feed_id"][0] 
        else: 
            return self.failHandshake("feed_id missing") 

        if params.has_key("format"):
            self.format = params["format"][0].lower() 
        else:
            return self.failHandshake("format missiong") 

        if params.has_key("isFront"): 
            self.isFront = params["isFront"][0].lower() 
        else:
            return self.failHandshake("isFront missing")

        self.factory.register(self,self.feed_id,self.format,self.isFront) 
        ## libWebsocket need specific subprotocol
        if len(request.protocols)>0: 
            return (request.protocols[0]) 
        else: 
            return 


    def onOpen(self):
        logger.debug("onOpen() called,welcome aboard! checking... feed_id=%s,format=%s,isFront=%s",self.feed_id,self.format,self.isFront) 

    def storeJsonStreams(self,data):
        if data.has_key("resource"):
            tup = data["resource"].split("/") 
            feed_id = tup[-2] 
            dataORcommand = tup[-1] 
            if self.feed_id != feed_id: 
                raise ValueError,("self.feed_id != feed_id") 
            for i in range(len(data[dataORcommand])): 
                element = data[dataORcommand][i] 
                timestamp = time.gmtime(element["current_value"]["timestamp"])
                timestamp = time.strftime("%d-%b-%Y %H:%M:%S",timestamp) 
                if element["id"] == "d_image": 
                    image = buffer(str(element["current_value"]["value"]))
                    db.insert_image("'%s'"%feed_id,"TIMESTAMP '%s'"%timestamp,image) 
                else: 
                    fields = ["feed_id","stream_id","updated_at","current_value"] 
                    values = ["'%s'"%feed_id,"'%s'"%element["id"],"TIMESTAMP '%s'"%timestamp,element["current_value"]["value"]] 
                    db.insert_point("robot_%s"%dataORcommand,fields,values) 
            if data.has_key("token"): 
                string = '''{"token": "%s"}'''%(str(data["token"]))
                self.sendMessage(string) 
            logger.debug("postgreSQL store a jsonStreams %s ",self.feed_id)

    def storeLargeObject(self,payload):
        timestamp = "'now'" 
        video = payload 
        #video = buffer(payload) 
        db.insert_video("'%s'"%self.feed_id,timestamp,video) 
        '''
        hd = file("video.mp4","ab")
        hd.write(payload) 
        hd.close() 
        '''
        logger.debug("postgreSQL store a video from %s",self.feed_id) 

    def onMessage(self,payload,isBinary):
        logger.debug("onMessage() called from feed_id=%s",self.feed_id) 
        if self.format=="video" and self.isFront=="false": 
            self.storeLargeObject(payload) 

            if self.feed_id in self.factory.videoFrontClients.keys():  
                self.factory.relayVideo(self.feed_id,payload) 
        elif self.format=="json": 
            data = json.loads(payload) 
            if data.has_key("method"):
                pass
            else:
                self.storeJsonStreams(data) 
                if self.isFront=="false":
                    logger.debug("autobahn received a datastream: %s ",data)
                    self.factory.relayDataJson(self.feed_id,payload) 
                else:
                    logger.debug("autobahn received a commandstream: %s ",data)
                    self.factory.relayCommandJson(self.feed_id,payload)

    def connectionLost(self,reason): 
        logger.debug("connectionLost() called for reason: ",reason)
        WebSocketServerProtocol.connectionLost(self,reason) 
        self.factory.unregister(self.feed_id,self.format,self.isFront) 


class IntorobotServerFactory(WebSocketServerFactory): 
    def __init__(self,url,debug=False,debugCodePaths=False): 
        WebSocketServerFactory.__init__(self,url,debug=debug,debugCodePaths=debugCodePaths)
        self.jsonFrontClients={} 
        self.jsonBackClients={} 
        self.videoFrontClients={} 
        self.videoBackClients={} 

    def register(self,client,feed_id,format,isFront): 
        if format=="json":
            if isFront=="false" and feed_id not in self.jsonBackClients.keys(): 
                self.jsonBackClients[feed_id]=client 
                logger.info("registered jsonBackClient,feed_id=%s,total jsonRobot NUM: %d ",feed_id,len(self.jsonBackClients)) 
            elif isFront=="true" and feed_id not in self.jsonFrontClients.keys(): 
                self.jsonFrontClients[feed_id]=client 
                logger.info("registered jsonFrontClient,feed_id=%s,total jsonUser NUM: %d ",feed_id,len(self.jsonFrontClients)) 
        elif format=="video":
            if isFront=="false" and feed_id not in self.videoBackClients.keys(): 
                self.videoBackClients[feed_id]=client
                logger.info("registered videoBackClient,feed_id=%s,total videoRobot NUM: %d ",feed_id,len(self.videoBackClients)) 
            elif isFront=="true" and feed_id not in self.videoFrontClients.keys():
                self.videoFrontClients[feed_id]=client
                logger.info("registered videoFrontClient,feed_id=%s,total videoUser NUM: %d ",feed_id,len(self.videoFrontClients)) 
        else:
            return self.protocol.failHandshake("Unkown format!") 
	    logger.warn("canot register a Unkown Format %s",format)



    def unregister(self,feed_id,format,isFront):
        if format=="json":
            if isFront=="false" and feed_id in self.jsonBackClients.keys(): 
                del self.jsonBackClients[feed_id]
                logger.info("unregistered jsonRobot,feed_id=%s",feed_id) 
            elif isFront=="true" and feed_id in self.jsonFrontClients.keys(): 
                del self.jsonFrontClients[feed_id] 
                logger.info("unregisted jsonUser,feed_id=%s",feed_id) 
        elif format=="video":
            if isFront=="false" and feed_id in self.videoBackClients.keys(): 
                del self.videoBackClients[feed_id]
                logger.info("unregistered VideoRobot,feed_id=%s",feed_id) 
            elif isFront=="true" and feed_id in self.videoFrontClients.keys():
                del self.videoFrontClients[feed_id]
                logger.info("unregistered VideoUser,feed_id=%s",feed_id) 

    def relayVideo(self,feed_id,payload): 
        if self.videoFrontClients.has_key(feed_id):
            logger.debug("relay video to %s",feed_id) 
            self.videoFrontClients[feed_id].sendMessage(payload,True) 
        
    def relayDataJson(self,feed_id,payload):
        if self.jsonFrontClients.has_key(feed_id): 
            logger.debug("relay data to %s",feed_id) 
            self.jsonFrontClients[feed_id].sendMessage(payload,False) 
    
    def relayCommandJson(self,feed_id,payload): 
        if self.jsonBackClients.has_key(feed_id): 
            logger.debug("relay data to %s",feed_id) 
            self.jsonBackClients[feed_id].sendMessage(payload,False) 

    def closeAllWebsocket(self):
        for (k,client) in self.jsonBackClients.items(): 
            client.loseConnection()  
        for (k,client) in self.jsonFrontClients.items(): 
            client.loseConnection() 
        for (k,client) in self.videoBackClients.items(): 
            client.loseConnection() 
        for (k,client) in self.videoFrontClients.items(): 
            client.loseConnection() 
        reactor.stop() 


import sys
import argparse
if __name__=='__main__':

    parser = argparse.ArgumentParser() 
    parser.add_argument("-p","--port",type=str,default="9000",help="spcify listenning port.")
    parser.add_argument("-l","--loglevel",type=str,default="debug",help="spcify logging level")
    parser.add_argument("-n","--loggername",type=str,default="autobahn9000",help="logger name") 
    parser.add_argument("-f","--filename",type=str,default="autobahn9000.log",help="logger file name")

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

    #factory = IntorobotServerFactory("ws://192.168.1.37:%s"%args.port) 
    #factory = IntorobotServerFactory("ws://162.243.154.223:%s"%args.port) 
    factory = IntorobotServerFactory("ws://127.0.0.1:%s"%args.port) 
    factory.protocol = IntorobotServerProtocol
    factory.setProtocolOptions(allowHixie76 = True) 
    listenWS(factory) 

    reactor.addSystemEventTrigger('before','shutdown',factory.closeAllWebsocket) 
    reactor.run() 
    
