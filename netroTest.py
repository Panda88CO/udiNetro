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
#from tzlocal import update_localzone

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
#netro1 = netroAccess(serial1, -3, -3, 7)
#netro2 = netroAccess(serial2, -3, -2, 7)
netro3 = netroAccess(serial3, -3, -2, 7)
#test1 = netro1.update_info()
zone_type = netro3.zone_config(1)
#moisture = netro3.update_moisture_info(-3)

#event1 = netro1.update_events(-5)
#print(test1)
#print(netro1.netro)
#test2 = netro2.update_info()
sch1=netro3.update_schedules(5)
for zone_info in netro3.netro['active_zones']:
    test = zone_info
    tst1= netro3.zone_status(zone_info)
    tst1a= netro3.zone_source(zone_info)
    tst1b= netro3.zone_config(zone_info)
    tst2= netro3.moisture(zone_info)
    tst3= netro3.moisture_slope(zone_info)
    tst3a= netro3.last_sch_start(zone_info)
    tst4= netro3.last_sch_end(zone_info)
    tst5= netro3.next_sch_start(zone_info)
    tst6= netro3.next_sch_end(zone_info)
    print(test, tst1, tst1a, tst1b, tst2, tst3, tst3a, tst4, tst5, tst6 )

#moisture = netro1.update_moisture_info(-5)
moisture1 = netro3.moisture(6)
moisture2 = netro3.moisture_slope(1)
#print(test2)

name1 = netro1.device_name()
type1= netro1.device_type()
zones = netro1.zone_list()
zone2 = netro1.zone_info(6)
event1 = netro1.update_events(-5)
print()
#chedules = netro1.update_schedules()

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