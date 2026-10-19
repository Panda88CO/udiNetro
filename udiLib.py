#!/usr/bin/env python3
"""
Polyglot TEST v3 node server 


MIT License
"""

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)

import os
from os import truncate
import re
import time
import math
import numbers 
import xml.etree.ElementTree as ET
from datetime import datetime


STATUS_CODE = {'STANDBY':0, 'SETUP':1, 'ONLINE':2, 'WATERING':3, 'OFFLINE':4, 'SLEEPING':5, 'POWEROFF':6,'ERROR':99,'UNKNOWN':99, 'VALID':0, 'EXECUTING':1, 'EXECUTED':2,'NO SCHEDULE':98, 'NO_SCHEDULE':98, None:99}
ZONE_CONFIG = {'SMART':0, 'ASSISTANT':1,'TIMER':2,'ERROR':99,'UNKNOWN':99, None:99}

def ctrl_status2ISY(self, status_str) -> int:
    logging.debug(f'ctrl_status2ISY : {status_str}')
    return STATUS_CODE.get(status_str, 99)

def zoneconfig2ISY(self,config_str) -> int:
    return ZONE_CONFIG.get(config_str, 99)

def node_queue(self, data):
    self.n_queue.append(data['address'])

def wait_for_node_done(self):
    while len(self.n_queue) == 0:
        time.sleep(0.1)
    self.n_queue.pop()

def mask2key (self, mask):
    logging.debug(f'mask2key : {mask}')
    return(int(round(math.log2(mask),0)))
    
def daysToMask (self, dayList):
    daysValue = 0 
    i = 0
    for day in self.daysOfWeek:
        if day in dayList:
            daysValue = daysValue + pow(2,i)
        i = i+1
    return(daysValue)


def daytimestr2epocTime(self, time_str) -> int:
    dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S")
    epoch_time = int(dt.timestamp())
    return(epoch_time)

def daystr2epocTime(self, time_str) -> int:
    dt = datetime.strptime(time_str, "%Y-%m-%d")
    epoch_time = int(dt.timestamp())
    return(epoch_time)


def maskToDays(self, daysValue):
    daysList = []
    for i in range(0,7):
        mask = pow(2,i)
        if (daysValue & mask) != 0 :
            daysList.append(self.daysOfWeek[i])
    return(daysList)


def bool2Nbr(self, bool):
    if bool == True:
        return(1)
    elif bool == False:
        return(0)
    else:
        return(99)
    
def round2ISY(self,nbr, res):
    if isinstance(nbr, numbers.Number):
        return(round(nbr, res))
    else:
        return(None)

def bool2ISY (self, data):
    if data is None:
        return(99)
    elif data:
        return(1)
    else:
        return(0)

def state2Nbr(self, val):
    if val == 'normal':
        return(0)
    elif val == 'alert':
        return(1)
    elif val == 'alertinvalid':
        return(97)    
    else:
        return(99)

def isy_value(self, value):
    if value is None:
        return (99)
    else:
        return(value)
    
def daylist2bin(self, daylist):
    sum = 0
    if 'sun' in daylist:
        sum = sum + 1
    if 'mon' in daylist:
        sum = sum + 2       
    if 'tue' in daylist:
        sum = sum + 4
    if 'wed' in daylist:
        sum = sum + 8
    if 'thu' in daylist:
        sum = sum + 16
    if 'fri' in daylist:
        sum = sum + 32
    if 'sat' in daylist:
        sum = sum + 64
    return(sum)


def season2ISY(self, season):
    logging.debug(f'season2ISY {season}')
    if season is not None:
        if season.upper() == 'WINTER':
            return(0)
        elif season.upper() == 'SUMMER':
            return(1)
        elif season != None:
            return(2)
        else:
            return (99)
    else:
        return(99)   


def state2ISY(self, state):
    logging.debug(f'state2ISY : state {state}')
    res = 99
    if state is not None:
        if state.lower() in ['offline', 'VALID']:
            res = 0
        elif state.lower() in['online', 'EXECUTING']:
            res = 1
        elif state.lower() in ['asleep', 'EXECUTED' ]:
            res = 2 
        elif state.lower() == 'overload':
            res = 4
        elif state.lower() == 'error':
            res = 5
        elif state.lower() == 'invalid':
            res = 97           
        else:          
            logging.error(f'Unknown state passed {state}')
            res = 99
    else:
        res = 99
    logging.debug(f'state2ISY {res} - {state}')
    return (res)


def sync_state2ISY(self, state):
    logging.debug(f'sync_state2ISY : state {state}')
    if state is not None:
        if state:
            return(1)
        else:          
            return(0)
    else:
        return(None)

#sync_state2ISY



def code2ISY(self, state):
    logging.debug(f'code2ISY : state {state}')
    if state is not None:
        if state.lower() == 'offline':
            return(0)
        elif state.lower() == 'ok':
            return(1)
        elif state.lower() == 'overload':
            return(4)
        elif state.lower() == 'error':
            return(5)
        elif state.lower() == 'invalid':
            return(97)       
        else:
            logging.error(f'Unknown state passed {state}')
            return(99)
    else:
        return(99)
    
def command_res2ISY(self, result):
    if result is not None:
        if result:
            return(0)
        else:          

            return(4)
    else:
        return(None)
    
def online2ISY(self, state):
    if state is not None:
        if state.lower() == 'online':
            return(1)
        else:
            return(0)
    else:
        return(None)

def openClose2ISY(self, state):
    if state is None:
        return(99)
    elif state == 'closed':
        return(0)
    else:
        return(1)

def cond2ISY(self, condition):
    if condition is None:
        return(99)
    else:
        return(condition)
    
def latch2ISY(self, state):
    if state is not None:
        if state in ['engaged', 'ChargePortLatchEngaged']:
            return(1)
        elif state in['blocking','ChargePortLatchBlocking']:
            return(2)
        elif state in ['disengaged','ChargePortLatchDisengaged']:
            return(0)
        elif state in ['ChargePortLatchSNA']:
            return(4)
        elif state in ['invalid']:
            return(97)
        else:
            return(99)
    else:
        return(99)

def sentry2ISY(self, state) -> int:
    try:
        if state is not None:
            if state == 'SentryModeStateOff':
                res = 1
            elif state == 'SentryModeStateIdle':
                res = 2
            elif state == 'SentryModeStateArmed':
                res = 3
            elif state == 'SentryModeStateAware':
                res = 4
            elif state == 'SentryModeStatePanic':
                res = 5
            elif state == 'SentryModeStateQuiet':
                res = 6    
            elif state == 'invalid':
                res = 97                   
            else:
                res = 99
        else:
            res = 99
        logging.debug(f'sentry2ISY = {res}')
        return (res)
    except Exception as e:
        logging.debug(f'Error sentry2ISY {state}:  {e} ')
        return(99)



def period2ISY(self, period):
    logging.debug(f'period2ISY {period}')
    if period is not None:
        if period.upper() == 'OFF_PEAK':
            return(0)
        elif period.upper() == 'PARTIAL_PEAK':
            return(1)
        elif period.upper() == 'PEAK':
            return(2)
        else:
            return (99) 
    else:
        return(99)

def CO_setDriver(self, key, value, Unit=None):
    logging.debug(f'CO_setDriver : {key} {value} {Unit}')
    try:
        if value is None:
            logging.debug('None value passed = seting 99, UOM 25')
            self.node.setDriver(key, 99, True, True, 25)
        elif isinstance(value, str) and value == 'invalid':
            self.node.setDriver(key, 97, True, True, 25)
        else:
            if Unit:
                self.node.setDriver(key, value, True, True, Unit)
            else:
                self.node.setDriver(key, value)
    except ValueError: #A non number was passed 
        logging.debug(f'Exception CO_setDriver : {key} {value} {Unit}')
        #self.node.setDriver(key, 99, True, True, 25)
        


    


def send_rel_temp_to_isy(self, temperature, stateVar):
    logging.debug(f'convert_temp_to_isy - {temperature}')
    if self.ISY_temp_unit == 0: # Celsius in ISY
        if self.messana_temp_unit == 'Celsius' or self.messana_temp_unit == 0:
            self.node.setDriver(stateVar, round(temperature,1), True, True, 4)
        else: # messana = Farenheit
            self.node.setDriver(stateVar, round(temperature*5/9,1), True, True, 17)
    elif  self.ISY_temp_unit == 1: # Farenheit in ISY
        if self.messana_temp_unit == 'Celsius' or self.messana_temp_unit == 0:
            self.node.setDriver(stateVar, round((temperature*9/5),1), True, True, 4)
        else:
            self.node.setDriver(stateVar, round(temperature,1), True, True, 17)
    else: # kelvin
        if self.messana_temp_unit == 'Celsius' or self.messana_temp_unit == 0:
            self.node.setDriver(stateVar, round((temperature,1), True, True, 4))
        else:
            self.node.setDriver(stateVar, round((temperature)*9/5,1), True, True, 17)


def send_temp_to_isy (self, temperature, stateVar):
    logging.debug(f'convert_temp_to_isy - {temperature}')
    if self.ISY_temp_unit == 0: # Celsius in ISY
        if self.messana_temp_unit == 'Celsius' or self.messana_temp_unit == 0:
            self.node.setDriver(stateVar, round(temperature,1), True, True, 4)
        else: # messana = Farenheit
            self.node.setDriver(stateVar, round((temperature-32)*5/9,1), True, True, 17)
    elif  self.ISY_temp_unit == 1: # Farenheit in ISY
        if self.messana_temp_unit == 'Celsius' or self.messana_temp_unit == 0:
            self.node.setDriver(stateVar, round((temperature*9/5+32),1), True, True, 4)
        else:
            self.node.setDriver(stateVar, round(temperature,1), True, True, 17)
    else: # kelvin
        if self.messana_temp_unit == 'Celsius' or self.messana_temp_unit == 0:
            self.node.setDriver(stateVar, round((temperature+273.15,1), True, True, 4))
        else:
            self.node.setDriver(stateVar, round((temperature+273.15-32)*9/5,1), True, True, 17)



def heartbeat(self):
    logging.debug('heartbeat: sending DON, waiting 5s, sending DOF')
    self.reportCmd('DON', 2)
    time.sleep(5)
    self.reportCmd('DOF', 2)

def handleLevelChange(self, level):
    logging.info(f'New log level: {level}')


def get_dynamic_profile_editors():
    """
    Return the dynamic JSON editors structure matching profile/editor/editors.xml and profile/nls/en_us.txt.
    """
    return [
        {
            "id": "IRRSTATE",
            "ranges": [
                {
                    "uom": "25",
                    "subset": "0,1,2,3,4,5,6,7,99",
                    "nls": "IRRSTATE",
                    "names": {
                        "0": "Standby",
                        "1": "Setup",
                        "2": "Online",
                        "3": "Watering",
                        "4": "Offline",
                        "5": "Sleeping",
                        "6": "Power Off",
                        "7": "Valve Error",
                        "99": "Unknown",
                    },
                }
            ],
        },
        {
            "id": "CTRLEN",
            "ranges": [
                {
                    "uom": "25",
                    "subset": "0,1,99",
                    "nls": "CTRLEN",
                    "names": {
                        "0": "Disabled",
                        "1": "Enabled",
                        "99": "Unknown",
                    },
                }
            ],
        },
        {
            "id": "SENSORSTAT",
            "ranges": [
                {
                    "uom": "25",
                    "subset": "0,1,98,99",
                    "nls": "SENSORSTAT",
                    "names": {
                        "0": "Offline",
                        "1": "Online",
                        "98": "Smart Schedule Enabled",
                        "99": "Unknown",
                    },
                }
            ],
        },
        {
            "id": "CONSTATUS",
            "ranges": [
                {
                    "uom": "25",
                    "subset": "0-3,99",
                    "nls": "CONSTATUS",
                    "names": {
                        "0": "Offline",
                        "1": "Online",
                        "2": "Sleeping",
                        "3": "Unknown",
                        "99": "Unknown",
                    },
                }
            ],
        },
        {
            "id": "NBRZONES",
            "ranges": [
                {
                    "uom": "70",
                    "min": 0,
                    "max": 16,
                }
            ],
        },
        {
            "id": "APICOUNT",
            "ranges": [
                {
                    "uom": "70",
                    "min": 0,
                    "max": 2000,
                }
            ],
        },
        {
            "id": "TEMPC",
            "ranges": [
                {
                    "uom": "4",
                    "min": -40,
                    "max": 105,
                    "prec": 1,
                },
                {
                    "uom": "25",
                    "subset": "98,99",
                    "nls": "TEMPNLS",
                    "names": {
                        "98": "No Temperature Data",
                        "99": "Unknown",
                    },
                },
            ],
        },
        {
            "id": "TEMPF",
            "ranges": [
                {
                    "uom": "17",
                    "min": -40,
                    "max": 221,
                    "prec": 1,
                },
                {
                    "uom": "25",
                    "subset": "98,99",
                    "nls": "TEMPNLS",
                    "names": {
                        "98": "No Temperature Data",
                        "99": "Unknown",
                    },
                },
            ],
        },
        {
            "id": "SETENABLE",
            "ranges": [
                {
                    "uom": "25",
                    "subset": "0,1",
                    "nls": "CTRLEN",
                    "names": {
                        "0": "Disabled",
                        "1": "Enabled",
                    },
                }
            ],
        },
        {
            "id": "SCHSOURCE",
            "ranges": [
                {
                    "uom": "25",
                    "subset": "0,1,2,99",
                    "nls": "SCHSOURCE",
                    "names": {
                        "0": "Netro Smart Schedule",
                        "1": "Netro Fixed Schedule",
                        "2": "Manual Watering",
                        "99": "Unknown",
                    },
                }
            ],
        },
        {
            "id": "SCHSTATUS",
            "ranges": [
                {
                    "uom": "25",
                    "subset": "0,1,2,98,99",
                    "nls": "SCHSTATUS",
                    "names": {
                        "0": "Awaiting Schedule start",
                        "1": "Schedule Executing",
                        "2": "Schedule Executed",
                        "98": "No Schedule Defined",
                        "99": "Unknown/Error",
                    },
                }
            ],
        },
        {
            "id": "STARTSTOP",
            "ranges": [
                {
                    "uom": "25",
                    "subset": "0,1",
                    "nls": "CTRLEN",
                    "names": {
                        "0": "Disabled",
                        "1": "Enabled",
                    },
                }
            ],
        },
        {
            "id": "MINDUR",
            "ranges": [
                {
                    "uom": "44",
                    "min": 0,
                    "max": 1440,
                    "prec": 0,
                },
                {
                    "uom": "25",
                    "subset": "99",
                    "nls": "UNKNLS",
                    "names": {
                        "99": "Unknown",
                    },
                },
            ],
        },
        {
            "id": "SETMINUTES",
            "ranges": [
                {
                    "uom": "44",
                    "min": 0,
                    "max": 120,
                    "prec": 0,
                }
            ],
        },
        {
            "id": "SETDAYS",
            "ranges": [
                {
                    "uom": "10",
                    "min": 0,
                    "max": 365,
                }
            ],
        },
        {
            "id": "ONOFFSTATE",
            "ranges": [
                {
                    "uom": "25",
                    "subset": "0,1",
                    "nls": "ONOFFSTATE",
                    "names": {
                        "0": "Off",
                        "1": "On",
                    },
                }
            ],
        },
        {
            "id": "ZONETYPE",
            "ranges": [
                {
                    "uom": "25",
                    "subset": "0,1,2,99",
                    "nls": "ZONETYPE",
                    "names": {
                        "0": "Smart",
                        "1": "Smart Basic",
                        "2": "Timer",
                        "99": "Unknown",
                    },
                }
            ],
        },
        {
            "id": "MOISTURE",
            "ranges": [
                {
                    "uom": "70",
                    "min": 0,
                    "max": 100,
                },
                {
                    "uom": "25",
                    "subset": "99",
                    "nls": "UNKNLS",
                    "names": {
                        "99": "Unknown",
                    },
                },
            ],
        },
        {
            "id": "MOISTSLOPE",
            "ranges": [
                {
                    "uom": "70",
                    "min": -100,
                    "max": 100,
                    "prec": 1,
                },
                {
                    "uom": "25",
                    "subset": "99",
                    "nls": "UNKNLS",
                    "names": {
                        "99": "Unknown",
                    },
                },
            ],
        },
        {
            "id": "SUNLIGHT",
            "ranges": [
                {
                    "uom": "36",
                    "min": 0,
                    "max": 10000,
                    "prec": 1,
                },
                {
                    "uom": "25",
                    "subset": "98,99",
                    "nls": "NOLIGHT",
                    "names": {
                        "98": "No light Data",
                        "99": "Unknown",
                    },
                },
            ],
        },
        {
            "id": "BATLEVEL",
            "ranges": [
                {
                    "uom": "51",
                    "min": 0,
                    "max": 100,
                },
                {
                    "uom": "25",
                    "subset": "98,99",
                    "nls": "BATNLS",
                    "names": {
                        "98": "No battery",
                        "99": "Unknown",
                    },
                },
            ],
        },
        {
            "id": "BOOLSTATE",
            "ranges": [
                {
                    "uom": "25",
                    "subset": "0,1,98,99",
                    "nls": "BOOLSTATE",
                    "names": {
                        "0": "False",
                        "1": "True",
                        "98": "N/A",
                        "99": "Unknown",
                    },
                }
            ],
        },
        {
            "id": "UNIXTIME",
            "ranges": [
                {
                    "uom": "151",
                    "min": 1748387733,
                    "max": 102063945730,
                },
                {
                    "uom": "25",
                    "subset": "98,99",
                    "nls": "SCHNLS",
                    "names": {
                        "98": "No Schedule Defined",
                        "99": "No Data",
                    },
                },
            ],
        },
    ]


def get_dynamic_profile_nodedefs():
    """
    Return the dynamic JSON nodedefs structure.
    Used for updateJsonProfile and as the primary source of driver names.
    """
    sensor_cmds = {
        "sends": [
            {"id": "DON"},
            {"id": "DOF"},
        ],
        "accepts": [
            {"id": "UPDATE", "name": "Update Data"},
        ],
    }

    return [
        {
            "id": "CONTROLLER",
            "nls": "NLSCTRL",
            "name": "Netro Irrigation Service",
            "icon": "Irrigation",
            "properties": [
                {"id": "ST", "editor": "CTRLEN", "name": "Controller Enabled"},
            ],
            "cmds": {
                "sends": [],
                "accepts": [],
            },
            "links": {"ctl": [], "rsp": []},
        },
        {
            "id": "IRRCTRL",
            "nls": "NLSIRRCTRL",
            "name": "Netro Irrigation Controller",
            "icon": "Irrigation",
            "properties": [
                {"id": "ST", "editor": "IRRSTATE", "name": "Controller State"},
                {"id": "GV1", "editor": "NBRZONES", "name": "Number Active Zones"},
                {"id": "GV3", "editor": "UNIXTIME", "name": "Next Start Time"},
                {"id": "GV4", "editor": "UNIXTIME", "name": "Previous End Time"},
                {"id": "GV5", "editor": "UNIXTIME", "name": "Last Offline Event"},
                {"id": "GV6", "editor": "UNIXTIME", "name": "Last Online Event"},
                {"id": "GV16", "editor": "BATLEVEL", "name": "Battery Level"},
                {"id": "GV17", "editor": "APICOUNT", "name": "Remaining API calls"},
                {"id": "GV19", "editor": "UNIXTIME", "name": "Last API Update"},
                {"id": "TIME", "editor": "UNIXTIME", "name": "Last Poll Time"},
            ],
            "cmds": {
                "sends": [
                    {"id": "DON"},
                    {"id": "DOF"},
                ],
                "accepts": [
                    {"id": "UPDATE", "name": "Update Data"},
                    {"id": "STOPWATER", "name": "Stop All Watering"},
                    {
                        "id": "SKIPDAYS",
                        "name": "Days to Skip Watering",
                        "parameters": [
                            {"id": "", "editor": "SETDAYS"},
                        ],
                    },
                    {
                        "id": "ENABLE",
                        "name": "Controller",
                        "parameters": [
                            {"id": "", "editor": "SETENABLE"},
                        ],
                    },
                ],
            },
            "links": {"ctl": [], "rsp": []},
        },
        {
            "id": "IRRZONE",
            "nls": "NLSZONE",
            "name": "Irrigation Zone",
            "icon": "Irrigation",
            "properties": [
                {"id": "ST", "editor": "SCHSTATUS", "name": "Zone Status"},
                {"id": "GV0", "editor": "NBRZONES", "name": "Zone Number"},
                {"id": "GV1", "editor": "ZONETYPE", "name": "Zone Type"},
                {"id": "GV2", "editor": "MOISTURE", "name": "Moisture Level (0-100)"},
                {"id": "GV3", "editor": "MOISTSLOPE", "name": "Moisture Slope"},
                {"id": "GV4", "editor": "UNIXTIME", "name": "Previous Start Time"},
                {"id": "GV5", "editor": "UNIXTIME", "name": "Previous End Time"},
                {"id": "GV6", "editor": "UNIXTIME", "name": "Next Start Time"},
                {"id": "GV7", "editor": "UNIXTIME", "name": "Next End Time"},
                {"id": "GV19", "editor": "UNIXTIME", "name": "Last Update"},
            ],
            "cmds": {
                "sends": [
                    {"id": "DON"},
                    {"id": "DOF"},
                ],
                "accepts": [
                    {"id": "STOPWATER", "name": "Stop Watering"},
                    {
                        "id": "WATER",
                        "name": "Water Zone",
                        "parameters": [
                            {"id": "DURATION", "editor": "SETMINUTES", "name": "Water Run Time"},
                            {"id": "DELAY", "editor": "SETMINUTES", "name": "Start Delay"},
                        ],
                    },
                ],
            },
            "links": {"ctl": [], "rsp": []},
        },
        {
            "id": "SENSORC",
            "nls": "NLSSENSOR",
            "name": "Irrigation Sensor",
            "icon": "Irrigation",
            "properties": [
                {"id": "ST", "editor": "MOISTURE", "name": "Moisture Level (0-100)(Estimated)"},
                {"id": "CLITEMP", "editor": "TEMPC", "name": "Temperature"},
                {"id": "GV2", "editor": "SUNLIGHT", "name": "Sun Light (LUX)"},
                {"id": "GV18", "editor": "UNIXTIME", "name": "Data Report Time"},
                {"id": "GV14", "editor": "BATLEVEL", "name": "Battery Level"},
                {"id": "GV15", "editor": "CONSTATUS", "name": "Connection Status"},
                {"id": "GV19", "editor": "UNIXTIME", "name": "Last Update"},
            ],
            "cmds": sensor_cmds,
            "links": {"ctl": [], "rsp": []},
        },
        {
            "id": "SENSORF",
            "nls": "NLSSENSOR",
            "name": "Irrigation Sensor",
            "icon": "Irrigation",
            "properties": [
                {"id": "ST", "editor": "MOISTURE", "name": "Moisture Level (0-100)(Estimated)"},
                {"id": "CLITEMP", "editor": "TEMPF", "name": "Temperature"},
                {"id": "GV2", "editor": "SUNLIGHT", "name": "Sun Light (LUX)"},
                {"id": "GV18", "editor": "UNIXTIME", "name": "Data Report Time"},
                {"id": "GV14", "editor": "BATLEVEL", "name": "Battery Level"},
                {"id": "GV15", "editor": "CONSTATUS", "name": "Connection Status"},
                {"id": "GV19", "editor": "UNIXTIME", "name": "Last Update"},
            ],
            "cmds": sensor_cmds,
            "links": {"ctl": [], "rsp": []},
        },
    ]


def get_dynamic_profile_nls():
    """
    Build the NLS key-value dictionary from the dynamic profile editors and nodedefs.
    """
    nls = {}
    for editor in get_dynamic_profile_editors():
        for rng in editor.get("ranges", []):
            nls_prefix = rng.get("nls")
            names = rng.get("names", {})
            if nls_prefix and names:
                for k, v in names.items():
                    nls[f"{nls_prefix}-{k}"] = v

    for nd in get_dynamic_profile_nodedefs():
        nd_id = nd["id"]
        nd_nls = nd.get("nls", nd_id)
        if "name" in nd:
            nls[f"ND-{nd_id}-NAME"] = nd["name"]
        if "icon" in nd:
            nls[f"ND-{nd_id}-ICON"] = nd["icon"]
        for prop in nd.get("properties", []):
            if "name" in prop:
                nls[f"ST-{nd_nls}-{prop['id']}-NAME"] = prop["name"]
        for cmd in nd.get("cmds", {}).get("accepts", []):
            if "name" in cmd:
                nls[f"CMD-{nd_nls}-{cmd['id']}-NAME"] = cmd["name"]
            for param in cmd.get("parameters", []):
                if param.get("id") and "name" in param:
                    nls[f"CMDP-{param['id']}-NAME"] = param["name"]

    return nls


_profile_driver_names = None


def get_profile_driver_names():
    """
    Extract the mapping of (nodeDefId, driver_id) -> display name.
    1. First takes names from dynamic profile definitions (get_dynamic_profile_nodedefs()).
    2. If not available (or for any missing entries), falls back to static profile files
       (profile/nodedef/nodedefs.xml and profile/nls/en_us.txt).
    Cached after the first load.
    """
    global _profile_driver_names
    if _profile_driver_names is not None:
        return _profile_driver_names

    _profile_driver_names = {}

    # 1. Try dynamic profile definitions first
    try:
        for nd in get_dynamic_profile_nodedefs():
            node_id = nd.get('id')
            for prop in nd.get('properties', []):
                driver_id = prop.get('id')
                name = prop.get('name')
                if node_id and driver_id and name:
                    _profile_driver_names[(node_id, driver_id)] = name
    except Exception as e:
        logging.warning(f'Could not load driver names from dynamic profile: {e}')

    # 2. Fall back to static profile directory if dynamic profile was unavailable or missing entries
    base_dir = os.path.dirname(os.path.abspath(__file__))
    xml_path = os.path.join(base_dir, 'profile', 'nodedef', 'nodedefs.xml')
    nls_path = os.path.join(base_dir, 'profile', 'nls', 'en_us.txt')

    if os.path.exists(xml_path) and os.path.exists(nls_path):
        try:
            st_labels = {}
            with open(nls_path, 'r', encoding='utf-8') as f:
                for line in f:
                    m = re.match(r'^ST-([\w\-]+)-([\w\-]+)-NAME\s*=\s*(.+)', line.strip())
                    if m:
                        nls, driver, label = m.groups()
                        st_labels[(nls, driver)] = label.strip()

            tree = ET.parse(xml_path)
            root = tree.getroot()
            for node_def in root.findall('.//nodeDef'):
                node_id = node_def.get('id')
                nls = node_def.get('nls')
                if not node_id or not nls:
                    continue
                for st in node_def.findall('.//st'):
                    driver_id = st.get('id')
                    if driver_id and (nls, driver_id) in st_labels:
                        if (node_id, driver_id) not in _profile_driver_names:
                            _profile_driver_names[(node_id, driver_id)] = st_labels[(nls, driver_id)]
        except Exception as e:
            logging.warning(f'Could not load driver names from static profile: {e}')

    return _profile_driver_names


def apply_profile_driver_names(self, node_id=None):
    """
    Populate or update 'name' in each driver dictionary of a node instance
    using definitions extracted from dynamic or static profiles.
    """
    target_id = node_id or getattr(self, 'id', None)
    if not target_id or not hasattr(self, 'drivers') or not self.drivers:
        return
    names = get_profile_driver_names()
    for d in self.drivers:
        driver_id = d.get('driver')
        if driver_id and (target_id, driver_id) in names:
            d['name'] = names[(target_id, driver_id)]