#!/usr/bin/env python

#####################################################
##
##   asynchronise access of database
##  
#####################################################

from twisted.enterprise import adbapi 
from twisted.internet import reactor 

dbpool = adbapi.ConnectionPool("psycopg2",database = "f2", user =
                               "f2", password = "123") 

def getId():
    return dbpool.runQuery("SELECT id FROM robot_commandstreams") 

def printResult(l):
    if l: 
        print l
    else:
        print "no such result" 

def insertCommand():
    q = "INSERT INTO robot_commandstreams (feed_id,stream_id,updated_at,current_value) VALUES ('53dde5e6a52633d704000003','c_left_speed','2014-08-20 09:10:18',10);" 
    reactor.callLater(1,insertCommand) 
    dbpool.runOperation(q) 


if __name__ == "__main__":
    getId().addCallback(printResult)
    reactor.callLater(1,insertCommand) 
    reactor.run() 

