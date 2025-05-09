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
netro1 = netroAccess(serial1)
netro2 = netroAccess(serial2)
test1 = netro1.get_info()
print(test1)
print()
test2 = netro2._callApi('GET', '/info.json')
print(test2)

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