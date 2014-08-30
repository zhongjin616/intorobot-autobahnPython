#!/usr/bin/env python
# coding=utf-8

##########################################
## TO RETRIEVE DATA POINT FORM DATABASE
#########################################

from twisted.enterprise import adbapi 
from twisted.internet import reactor 

dbpool = adbapi.ConnectionPool("pgdb",database="molmcdb",
                               host="localhost",user="postgres",password="123")

def printResult(l):
    print "printResult() called" 
    if l:
        print l
    else:
        print "No such result"
      

def getCommand(): 
    print "getCommand() called" 
    return dbpool.runQuery("select id from robot_commandstreams")
if __name__=="__main__":
    print "execute main" 
    print "dbpool", dbpool
    getCommand().addCallback(printResult)
    reactor.run() 
