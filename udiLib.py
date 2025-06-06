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

from os import truncate
import time
import math
import numbers 
from datetime import datetime


STATUS_CODE = {'STANDBY':0, 'SETUP':1, 'ONLINE':2, 'WATERING':3, 'OFFLINE':4, 'SLEEPING':5, 'POWEROFF':6,'ERROR':99,'UNKNOWN':99, 'VALID':0, 'EXECUTING':1, 'EXECUTED':2,'NO SCHEDULE':98}
ZONE_CONFIG = {'SMART':0, 'ASSISTANT':1,'TIMER':2,'ERROR':99,'UNKNOWN':99}

def ctrl_status2ISY(self, status_str) -> int:
    return(STATUS_CODE[status_str])

def zoneconfig2ISY(self,config_str) -> int:
    return(ZONE_CONFIG[config_str])

def node_queue(self, data):
    self.n_queue.append(data['address'])

def wait_for_node_done(self):
    while len(self.n_queue) == 0:
        time.sleep(0.1)
    self.n_queue.pop()

def mask2key (self, mask):
    logging.debug('mask2key : {mask}')
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
    logging.debug('season2ISY {season}')
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


def display2ISY(self,state):
    logging.debug(f'display2ISY : state {state}')
    if state is not None:
        if state == 'DisplayStateUnknown':
            return(0)
        elif state == 'DisplayStateOff':
            return(1)
        elif state == 'DisplayStateDim':
            return(2) 
        elif state == 'DisplayStateAccessory':
            return(3)
        elif state == 'DisplayStateOn':
            return(4)
        elif state == 'DisplayStateDriving':
            return(5)
        elif state == 'DisplayStateCharging':
            return(6)
        elif state == 'DisplayStateLock':
            return(7)
        elif state == 'DisplayStateSentry':
            return(8)
        elif state == 'DisplayStateDog':
            return(9)
        elif state == 'DisplayStateEntertainment':
            return(10)     
        elif state == 'invalid':
            return(97)                                                                                  
        else:          
            logging.error('Unknown state passed {state}')
            return(99)
    else:
        return(99)

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
            logging.error('Unknown state passed {state}')
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

def chargeState2ISY(self, state):
    if state is not None:
        if state in ['disconnected','ChargeStateDisconnected', 'DetailedChargeStateDisconnected']:
            return(0)
        elif state in ['nopower','ChargeStateNoPower', 'DetailedChargeStateNoPower']:
            return(1)          
        elif state in ['starting','ChargeStateStarting', 'DetailedChargeStateStarting']:
            return(2)
        elif state in ['charging',  'enable', 'ChargeStateCharging', 'DetailedChargeStateCharging']:
            return(3)
        elif state in ['stopped','ChargeStateStopped', 'DetailedChargeStateStopped']:
            return(4)
        elif state in ['complete','ChargeStateComplete', 'DetailedChargeStateComplete']:
            return(5)
        elif state in ['invalid',]:
            return(97)        
        else:
            return(99) 
    else:
        return(99)

def period2ISY(self, period):
    logging.debug('period2ISY {period}')
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
            #logging.debug('None value passed = seting 99, UOM 25')
            self.node.setDriver(key, 99, True, True, 25)
        elif isinstance(value, str) and value == 'invalid':
            self.node.setDriver(key, 97, True, True, 25)
        else:
            if Unit:
                self.node.setDriver(key, value, True, True, Unit)
            else:
                self.node.setDriver(key, value)
    except ValueError: #A non number was passed 
        self.node.setDriver(key, 99, True, True, 25)
        


    


def send_rel_temp_to_isy(self, temperature, stateVar):
    logging.debug('convert_temp_to_isy - {temperature}')
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
    logging.debug('convert_temp_to_isy - {temperature}')
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
    logging.debug('heartbeat: ' + str(self.hb))
    
    if self.hb == 0:
        self.reportCmd('DON',2)
        self.hb = 1
    else:
        self.reportCmd('DOF',2)
        self.hb = 0

def handleLevelChange(self, level):
    logging.info('New log level: {level}')        