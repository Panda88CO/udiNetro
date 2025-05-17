#!/usr/bin/env python3

### Your external service class
'''
MIT License
'''
import requests
import time
import json
from netroAPI import netroAccess
#from datetime import timedelta, datetime
from tzlocal import get_localzone

try:
    #import udi_interface
    from udi_interface import LOGGER, Custom, OAuth
    logging = LOGGER
except:
    import logging
    logging.basicConfig(level=30)

serial1 = 'd48afce15210'
serial2 = 'c82e18810de8'
serial3 = 'c82e1881d038'
netro1 = netroAccess(serial1)
netro2 = netroAccess(serial2)
#netro3 = netroAccess(serial3)
test1 = netro1.get_info()
event1 = netro1.get_events(-5)
print(test1)
print(netro1.netro)
#test2 = netro2.get_info()
sch1=netro1.get_schedules(7)

moisture = netro1.get_moisture_info(-5)
#print(test2)

name1 = netro1.device_name()
type1= netro1.device_type()
zones = netro1.zone_list()
zone2 = netro1.zone_info(6)
event1 = netro1.get_events(-5)
print()
#chedules = netro1.get_schedules()

testEN = netro1.set_status(0)
#time.sleep(1)
testEN = netro1.set_status(1)
test3 = netro1.set_watering(1,0,1)



payload = {}
#payload['event']=3
test2 =  netro1._callApi('GET', '/events.json', payload)

payload = {}
#payload['start_date']=3
#payload['end_date']=3
payload['zones']=[2,3]
test2 =  netro1._callApi('GET', '/events.json', payload)
payload = {}
payload['status']=0
test2 =  netro2._callApi('POST', '/set_status.json', payload)
test1 = netro2._callApi('GET', '/info.json')
print(test1)
#print(test3)
payload = {}
payload['status']=1
test2 =  netro2._callApi('POST', '/set_status.json', payload)
print(test2)
test1 = netro2._callApi('GET', '/info.json')
print(test1)