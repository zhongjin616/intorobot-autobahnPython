#!/usr/bin/env python
#---------------------------------------
#
#      INTERFACE FOR AUTOBAHN DATABASE #
#      AUTHOR: MOLMC
#
#---------------------------------------

from pg import *
import time

def csv(list):
    return ",".join([str(s) for s in list])


class autobahnDB:
    def __init__(self,dbname,host=None,user=None,passwd=None):
        #use pg.connect() to create a pgObject,which has access to database
#we can use pgObject's query method to execute SQL cmmand.
        self.conn = connect(dbname=dbname,host=host,user=user,passwd=passwd) 

    def query(self,q):
        return self.conn.query(q)

    def insert_point(self,table,fields,values):
        q = "INSERT INTO %s (%s) VALUES (%s);" \
                %(table,csv(fields),csv(values))
        self.conn.query(q) 

    def retrieve_point_by_timestamp(self,table,feed_id,stream_id,timestamp):
    	#tranlate Unix time to postgreSQL timestamp
    	timestamp = time.gmtime(timestamp)
        timestamp = time.strftime("%d-%b-%Y %H:%M:%S", timestamp)
        q = "SELECT current_value FROM %s WHERE (feed_id='%s') AND (stream_id='%s') AND (updated_at=%s)"%(table,feed_id,stream_id,"TIMESTAMP '%s'"%timestamp) 
        qr = self.conn.query(q) 
        value, = qr.getresult()[0]
        return value

    def retrieve_points(self,table,feed_id,stream_id):
        q = "SELECT current_value FROM %s WHERE (feed_id='%s') AND (stream_id='%s')"%(table,feed_id,stream_id)  
        qr = self.conn.query(q) 
        value = qr.getresult()
        return value




    def insert_large_object(self,buffer):
        self.conn.query("BEGIN")
        lohandle = self.conn.locreate(INV_WRITE)
        if lohandle:
            lohandle.open(INV_WRITE)
            lohandle.write(buffer)
            lohandle.close()
            self.conn.query("END")
            return lohandle.oid
        else:
            self.conn.query("ROLLBACK")
            raise IOError()
    
    def retrieve_large_object(self,oid):
        self.conn.query("BEGIN")
        lohandle = self.conn.getlo(oid)
        if lohandle:
            lohandle.open(INV_READ)
            size = lohandle.size()
            buffer = lohandle.read(size)
            lohandle.close()
            self.conn.query("END")
            return buffer
        else:
            self.conn.query("ROLLBACK")
            raise IOError() 

    def delete_large_object(self,oid):
        self.conn.query("BEGIN")
        lohandle = self.conn.getlo(oid)
        lohandel.unlink() 
        self.conn.query("END") 


    def insert_image(self,feed_id,timestamp,buffer):
        oid = self.insert_large_object(buffer)
        self.insert_point("robot_images",["feed_id","taken_time","raster"],[feed_id,timestamp,oid]) 


    def insert_video(self,feed_id,timestamp,buffer): 
        oid = self.insert_large_object(buffer)
        self.insert_point("robot_videos",["feed_id","taken_time","raster"],[feed_id,timestamp,oid]) 
        

    def get_image(self,feed_id,takentime): 
        qr = self.conn.query("select raster from robot_images where (feedid='%s') and (taken_time='%s')"%(feed_id,takentime)) 
        oid = qr.dictresulet()[0] 
        image = self.retrieve_large_object(oid)
        return image


    def get_video(self,feed_id,takentime): 
        qr = self.conn.query("select raster from robot_videos where (feedid='%s') and (taken_time='%s')"%(feed_id,takentime)) 
        oid = qr.dictresulet()[0] 
        image = self.retrieve_large_object(oid)
        return video


