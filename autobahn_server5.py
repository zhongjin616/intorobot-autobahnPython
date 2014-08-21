#!/usr/bin/env python

#################################################### 
#                                                  # 
#                                                  #
#       INTOROBOT PLATFORM                         #
#       AUTOBAHN SERVER                            #
#            Github                                #
#################################################### 

from autobahnDB import * #interface of postgreSQL 
from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketServerFactory,\
        WebSocketServerProtocol,\
        listenWS
from autobahn.websocket.protocol import ConnectionRequest,\
        parseHttpHeader

from autobahn.websocket import http
from six.moves import urllib
###To get access to Postgre database

#db = autobahnDB("exampledb",host="localhost",user="dbuser",passwd="dbuser") 

db = autobahnDB("molmcdb",host="localhost",user="postgres",passwd="123") 

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
        
    def processHandshake(self):
      '''
      Process WebSocket opening handshake request from client.
      '''
      ## only proceed when we have fully received the HTTP request line and all headers
      ##
      end_of_header = self.data.find(b"\x0d\x0a\x0d\x0a")
      if end_of_header >= 0:

         self.http_request_data = self.data[:end_of_header + 4]
         if self.debug:
            self.factory._log("received HTTP request:\n\n%s\n\n" % self.http_request_data)

         ## extract HTTP status line and headers
         ##
         (self.http_status_line, self.http_headers, http_headers_cnt) = parseHttpHeader(self.http_request_data)

         ## validate WebSocket opening handshake client request
         ##
         if self.debug:
            self.factory._log("received HTTP status line in opening handshake : %s" % str(self.http_status_line))
            self.factory._log("received HTTP headers in opening handshake : %s" % str(self.http_headers))

         ## HTTP Request line : METHOD, VERSION
         ##
         rl = self.http_status_line.split()
         if len(rl) != 3:
            return self.failHandshake("Bad HTTP request status line '%s'" % self.http_status_line)
         if rl[0].strip() != "GET":
            return self.failHandshake("HTTP method '%s' not allowed" % rl[0], http.METHOD_NOT_ALLOWED[0])
         vs = rl[2].strip().split("/")
         if len(vs) != 2 or vs[0] != "HTTP" or vs[1] not in ["1.1"]:
            return self.failHandshake("Unsupported HTTP version '%s'" % rl[2], http.UNSUPPORTED_HTTP_VERSION[0])

         ## HTTP Request line : REQUEST-URI
         ##
         self.http_request_uri = rl[1].strip()
         try:
            (scheme, netloc, path, params, query, fragment) = urllib.parse.urlparse(self.http_request_uri)

            ## FIXME: check that if absolute resource URI is given,
            ## the scheme/netloc matches the server
            if scheme != "" or netloc != "":
               pass

            ## Fragment identifiers are meaningless in the context of WebSocket
            ## URIs, and MUST NOT be used on these URIs.
            if fragment != "":
               return self.failHandshake("HTTP requested resource contains a fragment identifier '%s'" % fragment)

            ## resource path and query parameters .. this will get forwarded
            ## to onConnect()
            self.http_request_path = path
            self.http_request_params = urllib.parse.parse_qs(query)
         except:
            return self.failHandshake("Bad HTTP request resource - could not parse '%s'" % rl[1].strip())

         ## Host
         ##
         if not 'host' in self.http_headers:
            return self.failHandshake("HTTP Host header missing in opening handshake request")

         if http_headers_cnt["host"] > 1:
            return self.failHandshake("HTTP Host header appears more than once in opening handshake request")

         self.http_request_host = self.http_headers["host"].strip()

         if self.http_request_host.find(":") >= 0:
            (h, p) = self.http_request_host.split(":")
            try:
               port = int(str(p.strip()))
            except:
               return self.failHandshake("invalid port '%s' in HTTP Host header '%s'" % (str(p.strip()), str(self.http_request_host)))

            ## do port checking only if externalPort or URL was set
            if self.factory.externalPort:
               if port != self.factory.externalPort:
                  return self.failHandshake("port %d in HTTP Host header '%s' does not match server listening port %s" % (port, str(self.http_request_host), self.factory.externalPort))
            else:
               if self.debugCodePaths:
                  self.factory._log("skipping openening handshake port checking - neither WS URL nor external port set")

            self.http_request_host = h

         else:
            ## do port checking only if externalPort or URL was set
            '''
            if self.factory.externalPort:
               if not ((self.factory.isSecure and self.factory.externalPort == 443) or (not self.factory.isSecure and self.factory.externalPort == 80)):
                  return self.failHandshake("missing port in HTTP Host header '%s' and server runs on non-standard port %d (wss = %s)" % (str(self.http_request_host), self.factory.externalPort, self.factory.isSecure))
            else:
               if self.debugCodePaths:
                  self.factory._log("skipping openening handshake port checking - neither WS URL nor external port set")
            '''
            pass

         ## Upgrade
         ##
         if not 'upgrade' in self.http_headers:
            ## When no WS upgrade, render HTML server status page
            ##
            if self.webStatus:
               if 'redirect' in self.http_request_params and len(self.http_request_params['redirect']) > 0:
                  ## To specifiy an URL for redirection, encode the URL, i.e. from JavaScript:
                  ##
                  ##    var url = encodeURIComponent("http://autobahn.ws/python");
                  ##
                  ## and append the encoded string as a query parameter 'redirect'
                  ##
                  ##    http://localhost:9000?redirect=http%3A%2F%2Fautobahn.ws%2Fpython
                  ##    https://localhost:9000?redirect=https%3A%2F%2Ftwitter.com%2F
                  ##
                  ## This will perform an immediate HTTP-303 redirection. If you provide
                  ## an additional parameter 'after' (int >= 0), the redirection happens
                  ## via Meta-Refresh in the rendered HTML status page, i.e.
                  ##
                  ##    https://localhost:9000/?redirect=https%3A%2F%2Ftwitter.com%2F&after=3
                  ##
                  url = self.http_request_params['redirect'][0]
                  if 'after' in self.http_request_params and len(self.http_request_params['after']) > 0:
                     after = int(self.http_request_params['after'][0])
                     if self.debugCodePaths:
                        self.factory._log("HTTP Upgrade header missing : render server status page and meta-refresh-redirecting to %s after %d seconds" % (url, after))
                     self.sendServerStatus(url, after)
                  else:
                     if self.debugCodePaths:
                        self.factory._log("HTTP Upgrade header missing : 303-redirecting to %s" % url)
                     self.sendRedirect(url)
               else:
                  if self.debugCodePaths:
                     self.factory._log("HTTP Upgrade header missing : render server status page")
                  self.sendServerStatus()
               self.dropConnection(abort = False)
               return
            else:
               return self.failHandshake("HTTP Upgrade header missing", http.UPGRADE_REQUIRED[0])
         upgradeWebSocket = False
         for u in self.http_headers["upgrade"].split(","):
            if u.strip().lower() == "websocket":
               upgradeWebSocket = True
               break
         if not upgradeWebSocket:
            return self.failHandshake("HTTP Upgrade headers do not include 'websocket' value (case-insensitive) : %s" % self.http_headers["upgrade"])

         ## Connection
         ##
         if not 'connection' in self.http_headers:
            return self.failHandshake("HTTP Connection header missing")
         connectionUpgrade = False
         for c in self.http_headers["connection"].split(","):
            if c.strip().lower() == "upgrade":
               connectionUpgrade = True
               break
         if not connectionUpgrade:
            return self.failHandshake("HTTP Connection headers do not include 'upgrade' value (case-insensitive) : %s" % self.http_headers["connection"])

         ## Sec-WebSocket-Version PLUS determine mode: Hybi or Hixie
         ##
         if not 'sec-websocket-version' in self.http_headers:
            if self.debugCodePaths:
               self.factory._log("Hixie76 protocol detected")
            if self.allowHixie76:
               version = 0
            else:
               return self.failHandshake("WebSocket connection denied - Hixie76 protocol mode disabled.")
         else:
            if self.debugCodePaths:
               self.factory._log("Hybi protocol detected")
            if http_headers_cnt["sec-websocket-version"] > 1:
               return self.failHandshake("HTTP Sec-WebSocket-Version header appears more than once in opening handshake request")
            try:
               version = int(self.http_headers["sec-websocket-version"])
            except:
               return self.failHandshake("could not parse HTTP Sec-WebSocket-Version header '%s' in opening handshake request" % self.http_headers["sec-websocket-version"])

         if version not in self.versions:

            ## respond with list of supported versions (descending order)
            ##
            sv = sorted(self.versions)
            sv.reverse()
            svs = ','.join([str(x) for x in sv])
            return self.failHandshake("WebSocket version %d not supported (supported versions: %s)" % (version, svs),
                                      http.BAD_REQUEST[0],
                                      [("Sec-WebSocket-Version", svs)])
         else:
            ## store the protocol version we are supposed to talk
            self.websocket_version = version

         ## Sec-WebSocket-Protocol
         ##
         if 'sec-websocket-protocol' in self.http_headers:
            protocols = [str(x.strip()) for x in self.http_headers["sec-websocket-protocol"].split(",")]
            # check for duplicates in protocol header
            pp = {}
            for p in protocols:
               if p in pp:
                  return self.failHandshake("duplicate protocol '%s' specified in HTTP Sec-WebSocket-Protocol header" % p)
               else:
                  pp[p] = 1
            # ok, no duplicates, save list in order the client sent it
            self.websocket_protocols = protocols
         else:
            self.websocket_protocols = []

         ## Origin / Sec-WebSocket-Origin
         ## http://tools.ietf.org/html/draft-ietf-websec-origin-02
         ##
         if self.websocket_version < 13 and self.websocket_version != 0:
            # Hybi, but only < Hybi-13
            websocket_origin_header_key = 'sec-websocket-origin'
         else:
            # RFC6455, >= Hybi-13 and Hixie
            websocket_origin_header_key = "origin"

         self.websocket_origin = None
         if websocket_origin_header_key in self.http_headers:
            if http_headers_cnt[websocket_origin_header_key] > 1:
               return self.failHandshake("HTTP Origin header appears more than once in opening handshake request")
            self.websocket_origin = self.http_headers[websocket_origin_header_key].strip()
         else:
            # non-browser clients are allowed to omit this header
            pass

         ## Sec-WebSocket-Key (Hybi) or Sec-WebSocket-Key1/Sec-WebSocket-Key2 (Hixie-76)
         ##
         if self.websocket_version == 0:
            for kk in ['Sec-WebSocket-Key1', 'Sec-WebSocket-Key2']:
               k = kk.lower()
               if not k in self.http_headers:
                  return self.failHandshake("HTTP %s header missing" % kk)
               if http_headers_cnt[k] > 1:
                  return self.failHandshake("HTTP %s header appears more than once in opening handshake request" % kk)
               try:
                  key1 = self.parseHixie76Key(self.http_headers["sec-websocket-key1"].strip())
                  key2 = self.parseHixie76Key(self.http_headers["sec-websocket-key2"].strip())
               except:
                  return self.failHandshake("could not parse Sec-WebSocket-Key1/2")
         else:
            if not 'sec-websocket-key' in self.http_headers:
               return self.failHandshake("HTTP Sec-WebSocket-Key header missing")
            if http_headers_cnt["sec-websocket-key"] > 1:
               return self.failHandshake("HTTP Sec-WebSocket-Key header appears more than once in opening handshake request")
            key = self.http_headers["sec-websocket-key"].strip()
            if len(key) != 24: # 16 bytes => (ceil(128/24)*24)/6 == 24
               return self.failHandshake("bad Sec-WebSocket-Key (length must be 24 ASCII chars) '%s'" % key)
            if key[-2:] != "==": # 24 - ceil(128/6) == 2
               return self.failHandshake("bad Sec-WebSocket-Key (invalid base64 encoding) '%s'" % key)
            for c in key[:-2]:
               if c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/":
                  return self.failHandshake("bad character '%s' in Sec-WebSocket-Key (invalid base64 encoding) '%s'" % (c, key))

         ## Sec-WebSocket-Extensions
         ##
         self.websocket_extensions = []
         if 'sec-websocket-extensions' in self.http_headers:

            if self.websocket_version == 0:
               return self.failHandshake("HTTP Sec-WebSocket-Extensions header encountered for Hixie-76")
            else:
               if http_headers_cnt["sec-websocket-extensions"] > 1:
                  return self.failHandshake("HTTP Sec-WebSocket-Extensions header appears more than once in opening handshake request")
               else:
                  ## extensions requested/offered by client
                  ##
                  self.websocket_extensions = self._parseExtensionsHeader(self.http_headers["sec-websocket-extensions"])

         ## For Hixie-76, we need 8 octets of HTTP request body to complete HS!
         ##
         if self.websocket_version == 0:
            if len(self.data) < end_of_header + 4 + 8:
               return
            else:
               key3 =  self.data[end_of_header + 4:end_of_header + 4 + 8]
               if self.debug:
                  self.factory._log("received HTTP request body containing key3 for Hixie-76: %s" % key3)

         ## Ok, got complete HS input, remember rest (if any)
         ##
         if self.websocket_version == 0:
            self.data = self.data[end_of_header + 4 + 8:]
         else:
            self.data = self.data[end_of_header + 4:]

         ## store WS key
         ##
         if self.websocket_version == 0:
            self._wskey = (key1, key2, key3)
         else:
            self._wskey = key

         ## WebSocket handshake validated => produce opening handshake response

         ## Now fire onConnect() on derived class, to give that class a chance to accept or deny
         ## the connection. onConnect() may throw, in which case the connection is denied, or it
         ## may return a protocol from the protocols provided by client or None.
         ##
         request = ConnectionRequest(self.peer,
                                     self.http_headers,
                                     self.http_request_host,
                                     self.http_request_path,
                                     self.http_request_params,
                                     self.websocket_version,
                                     self.websocket_origin,
                                     self.websocket_protocols,
                                     self.websocket_extensions)
         self._onConnect(request) 


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
            logger.warn("canot register a Unkown Format %s",format)
            return self.protocol.failHandshake("Unkown format!") 



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


import argparse
if __name__=='__main__':

    parser = argparse.ArgumentParser() 
    parser.add_argument("-i","--ip",type=str,default="127.0.0.1",help="spcify listenning ip address.")
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
    factory = IntorobotServerFactory("ws://{}:{}".format(args.ip, args.port))  
    factory.protocol = IntorobotServerProtocol
    factory.setProtocolOptions(allowHixie76 = True) 
    listenWS(factory) 

    reactor.addSystemEventTrigger('before','shutdown',factory.closeAllWebsocket) 
    reactor.run() 
    
