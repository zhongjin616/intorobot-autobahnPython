#!/usr/bin/env python
# coding=utf-8

##########################################
## TO RETRIEVE DATA POINT FORM DATABASE
#########################################

from autobahnDB import *


world =autobahnDB("molmcdb",host="localhost",user="postgres",passwd="123")

value = world.retrieve_point_by_timestamp("datastreams","11212","d_left_speed",1405556411) 

print "robot 11212 d_left_speed at 1405556411 is: ",value

points=world.retrieve_points("datastreams","11212","d_left_speed") 
print "d_left_speed points is: ",points 

