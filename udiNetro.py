#!/usr/bin/env python3

import sys
try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=20)
import threading
import json
import re
import time

#from netroAPI import netroType
from datetime import timedelta, datetime
#from tzlocal import get_localzone
from netroController import netroController
from netroSensor import netroSensor
VERSION = '0.0.6'

class netroStart(udi_interface.Node):
    from  udiLib import handleLevelChange, node_queue, command_res2ISY, code2ISY, wait_for_node_done ,  cond2ISY,  mask2key, heartbeat, state2ISY, sync_state2ISY, bool2ISY, online2ISY, CO_setDriver, openClose2ISY
    from basic_api import netroType
    def __init__(self, polyglot, primary, address, name ):
        super(netroStart, self).__init__(polyglot, primary, address, name)
        logging.info(f'_init_ Netro Controller {VERSION}')
        logging.setLevel(10)
        logging.debug('Init Message system')
        self.poly = polyglot
        self.node = None
        self.EVENT_DAYS = -3
        self.SCH_DAYS = 7
        self.MOIST_DAYS = -4
        self.paramsProcessed = False
        self.customParameters = Custom(self.poly, 'customparams')
        #self.portalData = Custom(self.poly, 'customNSdata')
        self.Notices = Custom(polyglot, 'notices')
        self.ISYforced = False
        self.initialized = False
        self.primary = primary
        self.address = address
        self.name = name
        polyglot.subscribe(polyglot.CUSTOMPARAMS, self.customParamsHandler)
        polyglot.subscribe(polyglot.CONFIGDONE, self.configDoneHandler)
        #polyglot.subscribe(polyglot.ADDNODEDONE, TEV.node_queue)        
        polyglot.subscribe(polyglot.LOGLEVEL, self.handleLevelChange)
        polyglot.subscribe(polyglot.NOTICES, self.handleNotices)
        #polyglot.subscribe(polyglot.POLL, self.systemPoll)        
        #polyglot.subscribe(polyglot.WEBHOOK, self.webhook)
        #logging.debug('Calling start')
        #olyglot.subscribe(polyglot.START, self.start, 'controller')
        #polyglot.subscribe(polyglot.CUSTOMNS, self.customNSHandler)
        #polyglot.subscribe(polyglot.OAUTH, self.oauthHandler)
        #polyglot.subscribe(polyglot.ADDNODEDONE, self.node_queue)
        self.hb = 0
        self.connected = False
        self.nodeDefineDone = False
        self.poly.updateProfile()
        self.poly.ready()
        self.node = self.poly.getNode(address)
        self.customParam_done = False
        self.config_done = False

        self.serialID_list = []
        self.node_dict = {}

        logging.info('Controller init DONE')
        logging.debug(f'drivers ; {self.drivers}')

        self.poly.Notices.clear()
        self.poly.updateProfile()
        assigned_primary_addresses = ['controller']
        #self.poly.setCustomParamsDoc()

        while not self.customParam_done  or not self.config_done :
        #while not self.config_done and not self.portalReady :
            logging.info(f'Waiting for node to initialize {self.customParam_done} {self.config_done}')
            time.sleep(1)
        
        logging.debug(f'Detected devices : {self.serialID_list}')

        if len(self.serialID_list) == 0:
            self.poly.Notices['No serial IDs input in configuration folder - exiting']
            time.sleep(10)
            sys.exit()
   
        logging.debug(f'Instanciating nodes for {self.serialID_list}')
        for indx, serial_nbr in enumerate(self.serialID_list):
            logging.debug(f'Instanciating nodes for {serial_nbr}')
            dev_type, name  = self.netroType(serial_nbr)
            logging.debug(f'Name : {name}, {dev_type }')
            if dev_type == 'controller':
                name = self.poly.getValidName(name)
                self.node_dict[serial_nbr] = netroController(self.poly, serial_nbr, serial_nbr, name, self.EVENT_DAYS, self.MOIST_DAYS, self.SCH_DAYS)
                assigned_primary_addresses.append(serial_nbr)
            elif dev_type == 'sensor':
                name = self.poly.getValidName(name)
                self.node_dict[serial_nbr] = netroSensor(self.poly, serial_nbr, serial_nbr, name )
                assigned_primary_addresses.append(serial_nbr)
            time.sleep(1)

        time.sleep(10)
        logging.debug(f'Scanning db for extra nodes : {assigned_primary_addresses}')

        for indx, node  in enumerate(self.nodes_in_db):
            #node = self.nodes_in_db[nde]
            logging.debug(f'Scanning db for unused primary nodes  : {node}')
            if node['primaryNode'] not in assigned_primary_addresses:
                logging.debug('Removing node : {} {}'.format(node['name'], node))
                self.poly.delNode(node['address'])
            

        self.update_all_drivers()

        self.poly.Notices['done'] = 'Initialization process completed'
        self.initialized = True
        time.sleep(2)
        self.poly.Notices.clear()



    def check_config(self):
        self.nodes_in_db = self.poly.getNodesFromDb()
        #self.config_done= True


    def configDoneHandler(self):
        logging.debug('configDoneHandler - config_done')
        # We use this to discover devices, or ask to authenticate if user has not already done so
        self.poly.Notices.clear()
        self.nodes_in_db = self.poly.getNodesFromDb()
        self.config_done= True
 



    def handleNotices(self, level):
        logging.info('handleNotices:')
       
    def customParamsHandler(self, userParams):
        self.customParameters.load(userParams)
        logging.debug(f'customParamsHandler called {userParams}')
        IDerror = False
        try: 
            if 'SERIALID' in userParams:
                if self.customParameters['SERIAL'] != 'Input list of serial id(s) (space separated)':
                    temp_list = str(self.customParameters['SERIALID']).split()
                    for indx, serial in enumerate(temp_list):
                        if not bool(re.match(r'^([0-9A-Fa-f])',serial)):
                            self.poly.Notices['IDERROR'] = f'Illegal serial number detected {serial}'
                            IDerror = True
                    if not IDerror:
                        self.serialID_list = temp_list
               
            else:
                logging.warning('No serialID found')
                self.customParameters['SERIALID'] = 'Input list of serial numbers (space separated)'
                self.poly.Notices['SERIALID'] = 'SerialID(s) not specified'
            
            if 'EVENT_DAYS' in userParams:
                if  isinstance(self.customParameters['EVENT_DAYS'], int):
                    self.EVENT_DAYS = self.customParameters['EVENT_DAYS']
            else:
                self.EVENT_DAYS = -5
    
            if 'SCH_DAYS' in userParams:
                if  isinstance(self.customParameters['SCH_DAYS'], int):
                    self.SCH_DAYS = self.customParameters['SCH_DAYS']
            else:
                self.SCH_DAYS = 7
            if 'MOIST_DAYS' in userParams:
                if  isinstance(self.customParameters['MOIST_DAYS'], int):
                    self.MOIST_DAYS = self.customParameters['MOIST_DAYS']
            else:
                 self.MOIST_DAYS = -3
            self.customParam_done = True

            logging.debug('customParamsHandler finish ')
        except Exception as e:
            logging.error(f'Error detected during custome Param parsing {e}')
        
   

    '''
    def start(self):
        logging.info('start main node')
        self.poly.Notices.clear()
        self.poly.updateProfile()
        assigned_primary_addresses = ['controller']
        #self.poly.setCustomParamsDoc()
        
        while not self.customParam_done  or not self.config_done :
        #while not self.config_done and not self.portalReady :
            logging.info(f'Waiting for node to initialize {self.customParam_done} {self.config_done}')
            #logging.debug(f' 1 2 3: {} {} {} {}'.format(self.customParam_done, , self.config_done))
            time.sleep(1)
        
        logging.debug(f'Detected devices : {self.serialID_list}')

        if len(self.serialID_list) == 0:
            self.poly.Notices['No serial IDs input in configuration folder - exiting']
            time.sleep(10)
            sys.exit()
        for indx, device in enumerate (self.serialID_list):
            logging.debug(f'Instanciating nodes for {device}')
            api = netroAccess(device, self.EVENT_DAYS, self.MOIST_DAYS, self.SCH_DAYS)
            logging.debug(f'Device Type: {api.device_type()}')
            if api.device_type() == 'controller':
                name = self.poly.getValidName(api.device_name())
                self.node_dict[device] = netroController(self.poly, device, device, name, api )
                assigned_primary_addresses.append(device)
            elif api.device_type() == 'sensor':
                name = self.poly.getValidName(api.device_name())
                self.node_dict[device] = netroSensor(self.poly, device, device, name , api )
                assigned_primary_addresses.append(device)
       
           
        #logging.debug(f'Scanning db for extra nodes : {assigned_primary_addresses}')
        #for indx, node  in enumerate(self.nodes_in_db):
        #    #node = self.nodes_in_db[nde]
        #    logging.debug(f'Scanning db for node : {node}')
        #    if node['primaryNode'] not in assigned_primary_addresses:
        #        logging.debug('Removing node : {} {}'.format(node['name'], node))
        #        self.poly.delNode(node['address'])
            

        self.poly.Notices['done'] = 'Initialization process completed'
        self.initialized = True
        time.sleep(2)
        self.poly.Notices.clear()
    '''

    def validate_params(self):
        logging.debug('validate_params: {}'.format(self.Parameters.dump()))
        self.paramsProcessed = True


    def stop(self):
        self.Notices.clear()
        #self.background_thread.stop()
        #if self.TEV:
        self.CO_setDriver('ST', 0, 25 )
        logging.debug('stop - Cleaning up')
        #self.scheduler.shutdown()
        self.poly.stop()
        sys.exit() # kill running threads


    '''
    def systemPoll(self, pollList):
        logging.debug(f'systemPoll - {pollList}')
    
        if 'longPoll' in pollList: 
            self.longPoll()
            if 'shortPoll' in pollList: #send short polls heart beat as shortpoll is not executed
                self.heartbeat()
        if 'shortPoll' in pollList:
            self.shortPoll()

    
    def shortPoll(self):
        pass:
        try:
            logging.info('Netro Controller shortPoll(HeartBeat)')
            self.heartbeat()



        except Exception:
            logging.info('Not all nodes ready:')

    def longPoll(self):
        try:
            logging.debug(f'long poll list - checking for token update required')

        except Exception:
            logging.info(f'Not all nodes ready:')
    '''

   


  

    def update_all_drivers(self):
        logging.debug('updateISYdrivers')


    def updateISYdrivers(self):
        
        logging.debug(f'Update main node {self.drivers}')
 

    def ISYupdate (self, command=None):
        logging.info(f'ISY-update status node  called')





    
    
    id = 'controller'


    commands = {  }


    drivers = [
            {'driver': 'ST', 'value': 99, 'uom': 25},   #car State                       
            ]

    
            # ST - node started
            # GV0 Access to TeslaApi
            # GV1 Number of EVs


if __name__ == "__main__":
    try:
        logging.info('Starting Netro Nodes')
        polyglot = udi_interface.Interface([])
        polyglot.start(VERSION)
        #polyglot.setCustomParamsDoc()
        Netro =netroStart(polyglot, 'controller', 'controller', 'Netro Irrigation')

        polyglot.ready()
        polyglot.runForever()

    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
