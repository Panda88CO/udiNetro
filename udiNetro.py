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

from netroAPI import netroAccess
from datetime import timedelta, datetime
from tzlocal import get_localzone
from netroController import netroController
from netroSensor import netroSensor
VERSION = '0.0.1'

class netroStart(udi_interface.Node):
    from  udiLib import node_queue, command_res2ISY, code2ISY, wait_for_node_done,tempUnitAdjust, display2ISY, sentry2ISY, setDriverTemp, cond2ISY,  mask2key, heartbeat, state2ISY, sync_state2ISY, bool2ISY, online2ISY, EV_setDriver, openClose2ISY

    def __init__(self, polyglot, primary, address, name ):
        super(netroStart, self).__init__(polyglot, primary, address, name)
        logging.info(f'_init_ Netro Controller {VERSION}')
        logging.setLevel(10)
        logging.debug('Init Message system')
        self.poly = polyglot
        self.node = None
        self.CELCIUS = 0
        self.FARENHEIT = 1 

        self.supportedParams = ['DIST_UNIT', 'TEMP_UNIT']
        self.paramsProcessed = False
        self.customParameters = Custom(self.poly, 'customparams')
        self.portalData = Custom(self.poly, 'customNSdata')
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
        polyglot.subscribe(polyglot.POLL, self.systemPoll)        
        #polyglot.subscribe(polyglot.WEBHOOK, self.webhook)
        logging.debug('Calling start')
        polyglot.subscribe(polyglot.START, self.start, 'controller')
        #polyglot.subscribe(polyglot.CUSTOMNS, self.customNSHandler)
        #polyglot.subscribe(polyglot.OAUTH, self.oauthHandler)
        #polyglot.subscribe(polyglot.ADDNODEDONE, self.node_queue)
        self.hb = 0
        self.connected = False
        self.nodeDefineDone = False

        self.poly.updateProfile()
        self.poly.ready()
        self.tempUnit = 0 # C
        self.distUnit = 0 # KM
        self.customParam_done = False
        self.config_done = False

        self.serialID_list = []
        self.nodelist = []

        logging.info('Controller init DONE')
        logging.debug(f'drivers ; {self.drivers}')

    def check_config(self):
        self.nodes_in_db = self.poly.getNodesFromDb()
        #self.config_done= True


    def configDoneHandler(self):
        logging.debug('configDoneHandler - config_done')
        # We use this to discover devices, or ask to authenticate if user has not already done so
        self.poly.Notices.clear()
        self.nodes_in_db = self.poly.getNodesFromDb()
        self.config_done= True
        try:
            self.tesla_api.getAccessToken()
        except ValueError:
            logging.warning('Access token is not yet available. Please authenticate.')
            self.poly.Notices['auth'] = 'Please initiate authentication'
        return

    def oauthHandler(self, token):
        # When user just authorized, pass this to your service, which will pass it to the OAuth handler
        self.tesla_api.oauthHandler(token)
        # Then proceed with device discovery
        self.configDoneHandler()

    def handleLevelChange(self, level):
        logging.info(f'New log level: {level}')

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
                        if not bool(re.match(r'^([0-9A-Fa-f]',serial)):
                            self.poly.Notices['IDERROR'] = f'Illegal serial number detected {serial}'
                            IDerror = True
                    if not IDerror:
                        self.serialID_list = temp_list
               
            else:
                logging.warning('No serialID found')
                self.customParameters['SERIALID'] = 'Input list of serial numbers (space separated)'
                self.poly.Notices['SERIALID'] = 'SerialID(s) not specified'
    
            if 'TEMP_UNIT' in userParams:
                if self.customParameters['TEMP_UNIT'] != 'C or F':
                    self.temp_unit = str(self.customParameters['TEMP_UNIT'])
                    if self.temp_unit[0].upper() not in ['C', 'F']:
                        logging.error(f'Unsupported temperatue unit {self.temp_unit}')
                        self.poly.Notices['temp'] = 'Unknown distance Unit specified'
            else:
                logging.warning('No TEMP_UNIT')
                self.customParameters['TEMP_UNIT'] = 'C or F'


            self.customParam_done = True

            logging.debug('customParamsHandler finish ')
        except Exception as e:
            logging.error(f'Error detected during custome Param parsing {e}')
        
   

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
            api = netroAccess(device)
            if api.device_type == 'controller':
                name = api.get_device_name()
                self.node_list[device] = netroController(self.poly, device, device, name, api )
                assigned_primary_addresses.append(device)
            elif api.device_type == 'sensor':
                self.node_list[device] = netroSensor(self.poly, device, device, 'sensor'+ device , api )
                assigned_primary_addresses.append(device)
       
           
        logging.debug(f'Scanning db for extra nodes : {assigned_primary_addresses}')

        for indx, node  in enumerate(self.nodes_in_db):
            #node = self.nodes_in_db[nde]
            logging.debug(f'Scanning db for node : {node}')
            if node['primaryNode'] not in assigned_primary_addresses:
                logging.debug('Removing node : {} {}'.format(node['name'], node))
                self.poly.delNode(node['address'])
            

        self.update_all_drivers()

        self.poly.Notices['done'] = 'Initialization process completed'
        self.initialized = True
        time.sleep(2)
        self.poly.Notices.clear()


    def validate_params(self):
        logging.debug('validate_params: {}'.format(self.Parameters.dump()))
        self.paramsProcessed = True


    def stop(self):
        self.Notices.clear()
        #self.background_thread.stop()
        #if self.TEV:
        self.EV_setDriver('ST', 0, 25 )
        logging.debug('stop - Cleaning up')
        #self.scheduler.shutdown()
        self.poly.stop()
        sys.exit() # kill running threads


    def systemPoll(self, pollList):
        logging.debug(f'systemPoll - {pollList}')
        if self.TEVcloud:
            if self.tesla_api.authenticated() and self.initialized:
                time_n = int(time.time())
                last_time = self.TEVcloud.teslaEV_GetTimestamp(self.EVid)
                logging.debug(f'tine now {time_n} , last_time {last_time}')
                if last_time is None:
                    code, state = self.TEVcloud.teslaEV_GetCarState(self.EVid)
                    if state:
                        self.EV_setDriver('ST', self.state2ISY(state), 25)
                        self.poly.Notices.delete('offline')
                    else:
                        self.poly.Notices['offline']='API connection Failure - please re-authenticate'
                        self.EV_setDriver('ST', 98, 25)
                            #self.TEVcloud.teslaEV_get_vehicles()
                elif isinstance(time_n, int) and isinstance(last_time, int):
                    if (time_n - last_time) > self.STATE_UPDATE_MIN * 60:
                        code, state = self.TEVcloud.teslaEV_GetCarState(self.EVid)
                        if state:
                            self.EV_setDriver('ST', self.state2ISY(state), 25)
                            self.poly.Notices.delete('offline')
                        else:
                            self.poly.Notices['offline']='API connection Failure - please re-authenticate'
                            self.EV_setDriver('ST', 98, 25)
                            #self.TEVcloud.teslaEV_get_vehicles()
                if 'longPoll' in pollList: 
                    self.longPoll()
                    if 'shortPoll' in pollList: #send short polls heart beat as shortpoll is not executed
                        self.heartbeat()
                if self.nbr_wall_conn != 0:
                        self.power_share_node.poll('all')
                if 'shortPoll' in pollList:
                    self.shortPoll()
                    if self.nbr_wall_conn != 0:
                        self.power_share_node.poll('critical')
            else:
                logging.info('Waiting for system/nodes to initialize')

    def shortPoll(self):
        try:
            logging.info('Tesla EV Controller shortPoll(HeartBeat)')
            self.heartbeat()
            if self.nbr_wall_conn != 0:
                self.power_share_node.poll('critical')


        except Exception:
            logging.info('Not all nodes ready:')

    def longPoll(self):
        try:
            logging.info('Tesla EV  Controller longPoll - connected = {}'.format(self.tesla_api.authenticated()))
            logging.debug(f'long poll list - checking for token update required')
            self.tesla_api.teslaEV_streaming_check_certificate_update(self.EVid) #We need to check if we need to update streaming server credentials
            if self.nbr_wall_conn != 0:
                self.power_share_node.poll('critical')
        except Exception:
            logging.info(f'Not all nodes ready:')


   


  

    def update_all_drivers(self):
        try:
            if self.data_flowing:
                logging.debug('updateISYdrivers')
                self.updateISYdrivers()
                logging.debug(f'climate updateISYdrivers {self.climateNode.node_ready()}')
                if self.climateNode.node_ready():
                    self.climateNode.updateISYdrivers()
                logging.debug(f'charge updateISYdrivers {self.chargeNode.node_ready()}')                
                if self.chargeNode.node_ready():
                    self.chargeNode.updateISYdrivers()
                    
                if self.nbr_wall_conn != 0: 
                    logging.debug(f'power share updateISYdrivers {self.power_share_node.node_ready()}')   
                    if self.power_share_node.node_ready():
                        self.power_share_node.updateISYdrivers()
        except Exception as e:
            logging.debug(f'All nodes may not be ready yet {e}')


    def updateISYdrivers(self):
        try:
            logging.debug(f'Update main node {self.drivers}')
            self.update_time()

            self.EV_setDriver('GV29', self.sync_state2ISY(self.tesla_api.stream_synched), 25)

            logging.info(f'updateISYdrivers - Status for {self.EVid}')
            self.EV_setDriver('GV1',self.display2ISY(self.TEVcloud.teslaEV_GetCenterDisplay(self.EVid)), 25)
            self.EV_setDriver('GV2', self.bool2ISY(self.TEVcloud.teslaEV_HomeLinkNearby(self.EVid)), 25)
            self.EV_setDriver('GV0', self.TEVcloud.teslaEV_nbrHomeLink(self.EVid), 25)

            self.EV_setDriver('GV3', self.bool2ISY(self.TEVcloud.teslaEV_GetLockState(self.EVid)), 25)
            if self.TEVcloud.teslaEV_GetDistUnit() == 1:
                self.EV_setDriver('GV4', self.TEVcloud.teslaEV_GetOdometer(self.EVid), 116)
            else:
                self.EV_setDriver('GV4', int(self.TEVcloud.teslaEV_GetOdometer(self.EVid)*1.6), 83)
            temp = self.TEVcloud.teslaEV_GetSentryState(self.EVid)
            logging.debug(f'teslaEV_GetSentryState {temp}')
            temp_val = self.sentry2ISY(temp)
            logging.debug(f'teslaEV_GetSentryState ISY {temp_val}')
            self.EV_setDriver('GV5', temp_val, 25)
            
            windows  = self.TEVcloud.teslaEV_GetWindowStates(self.EVid)
            logging.debug(f'teslaEV_GetSientryState ISY {windows}')
            if 'FrontLeft' not in windows:
                windows['FrontLeft'] = None
            if 'FrontRight' not in windows:
                windows['FrontRight'] = None
            if 'RearLeft' not in windows:
                windows['RearLeft'] = None
            if 'RearRight' not in windows:
                windows['RearRight'] = None
            self.EV_setDriver('GV6', windows['FrontLeft'], 25)
            self.EV_setDriver('GV7', windows['FrontRight'], 25)
            self.EV_setDriver('GV8', windows['RearLeft'], 25)
            self.EV_setDriver('GV9', windows['RearRight'], 25)
            
            #self.EV_setDriver('GV10', self.TEVcloud.teslaEV_GetSunRoofPercent(self.EVid), 51)
            #if self.TEVcloud.teslaEV_GetSunRoofState(self.EVid) != None:
            #    self.EV_setDriver('GV10', self.openClose2ISY(self.TEVcloud.teslaEV_GetSunRoofState(self.EVid)), 25)
    
            self.EV_setDriver('GV11', self.TEVcloud.teslaEV_GetTrunkState(self.EVid), 25)
            self.EV_setDriver('GV12', self.TEVcloud.teslaEV_GetFrunkState(self.EVid), 25)

            tire_psi = self.TEVcloud.teslaEV_getTpmsPressure(self.EVid)
            self.EV_setDriver('GV23', tire_psi['tmpsFr'], 138)
            self.EV_setDriver('GV24', tire_psi['tmpsFl'], 138)
            self.EV_setDriver('GV25', tire_psi['tmpsRr'], 138)
            self.EV_setDriver('GV26', tire_psi['tmpsRl'], 138)
            #if self.TEVcloud.location_enabled():
            location = self.TEVcloud.teslaEV_GetLocation(self.EVid)
            logging.debug(f'teslaEV_GetLocation {location}')
            if location['longitude']:
                logging.debug('GV17: {}'.format(round(location['longitude'], 2)))
                self.EV_setDriver('GV17', round(location['longitude'], 3), 56)
            else:
                logging.debug(f'GV17: NONE')
                self.EV_setDriver('GV17', None, 25)
            if location['latitude']:
                logging.debug('GV18: {}'.format(round(location['latitude'], 2)))
                self.EV_setDriver('GV18', round(location['latitude'], 3), 56)
            else:
                logging.debug('GV18: NONE')
                self.EV_setDriver('GV18', None, 25)
            #else:
            #    self.EV_setDriver('GV17', 98, 25)
            #    self.EV_setDriver('GV18', 98, 25)
        except Exception as e:
            logging.error(f'updateISYdriver main node failed: node may not be 100% ready {e}')

    def ISYupdate (self, command=None):
        logging.info(f'ISY-update status node  called')
        #code, state = self.TEVcloud.teslaEV_update_connection_status(self.EVid)
        self.update_all_drivers()
        #self.display_update()
        code, res = self.TEVcloud.teslaEV_GetCarState(self.EVid)
        self.EV_setDriver('ST', self.state2ISY(res), 25)
        if code in ['ok']:
             self.EV_setDriver('GV21', self.command_res2ISY(res),25)
        else:
            self.EV_setDriver('GV21', self.code2ISY(code),25)

    def evWakeUp (self, command):
        logging.info(f'EVwakeUp called')
        code, res = self.TEVcloud._teslaEV_wake_ev(self.EVid)
        logging.debug(f'Wake result {code} - {res}')
        if code in ['ok']:               
            time.sleep(2)
            self.update_all_drivers()
        if code in ['ok']:
             self.EV_setDriver('GV21', self.command_res2ISY(res),25)
             self.EV_setDriver('ST', self.state2ISY(res), 25)
        else:
            self.EV_setDriver('GV21', self.code2ISY(code),25)


    def evHonkHorn (self, command):
        logging.info(f'EVhonkHorn called')        
        code, res = self.TEVcloud.teslaEV_HonkHorn(self.EVid)
        logging.info(f'return  {code} - {res}')

   
        if code in ['ok']:
            self.EV_setDriver('GV21', self.command_res2ISY(res),25)
            self.EV_setDriver('ST', 1, 25)
        else:
            self.EV_setDriver('GV21', self.code2ISY(code),25)
            code, res = self.TEVcloud.teslaEV_GetCarState(self.EVid)
            self.EV_setDriver('ST', self.state2ISY(res), 25)


    def evFlashLights (self, command):
        logging.info(f'EVflashLights called')
        code, res = self.TEVcloud.teslaEV_FlashLights(self.EVid)
        logging.info(f'return  {code} - {res}')

        if code in ['ok']:
             self.EV_setDriver('GV21', self.command_res2ISY(res),25)
        else:
            self.EV_setDriver('GV21', self.code2ISY(code),25)
        code, res = self.TEVcloud.teslaEV_GetCarState(self.EVid)
        self.EV_setDriver('ST', self.state2ISY(res), 25)

        #self.forceUpdateISYdrivers()

    def evControlDoors (self, command):
        logging.info(f'EVctrlDoors called')
        #self.TEVcloud.teslaEV_Wake(self.EVid)
 
        doorCtrl = int(float(command.get('value')))
        if doorCtrl == 1:
            cmd = 'lock'
            #code, red =  self.TEVcloud.teslaEV_Doors(self.EVid, 'unlock')
            #self.EV_setDriver('GV3', doorCtrl )
        elif doorCtrl == 0:
            cmd = 'unlock'
            #code, res =  self.TEVcloud.teslaEV_Doors(self.EVid, 'lock')
            #self.EV_setDriver('GV3', doorCtrl )            
        else:
            logging.error(f'Unknown command for evControlDoors {command}')
            self.EV_setDriver('GV21', self.command_res2ISY('error'), 25)
            return('error', 'code wrong')
        code, res =  self.TEVcloud.teslaEV_Doors(self.EVid, cmd)
        logging.info(f'return  {code} - {res}')
        self.EV_setDriver('GV3', doorCtrl, 25)
        if code in ['ok']:
             self.EV_setDriver('GV21', self.command_res2ISY(res),25)
        else:
            self.EV_setDriver('GV21', self.code2ISY(code),25)
            self.EV_setDriver('GV3', None, 25)
        code, res = self.TEVcloud.teslaEV_GetCarState(self.EVid)
        self.EV_setDriver('ST', self.state2ISY(res), 25)


    def evPlaySound (self, command):
        logging.info(f'evPlaySound called')
        #self.TEVcloud.teslaEV_Wake(self.EVid)
        sound = int(float(command.get('value')))
        if sound == 0 or sound == 2000: 
            code, res = self.TEVcloud.teslaEV_PlaySound(self.EVid, sound)
            if code in ['ok']:
                self.EV_setDriver('GV21', self.command_res2ISY(res),25)
            else:
                self.EV_setDriver('GV21', self.code2ISY(code),25)
        code, res = self.TEVcloud.teslaEV_GetCarState(self.EVid)
        self.EV_setDriver('ST', self.state2ISY(res), 25)

    def evSentryMode (self, command):
        logging.info(f'evSentryMode called')
        #self.TEVcloud.teslaEV_Wake(self.EVid)
        ctrl = int(float(command.get('value')))
     
        code, res = self.TEVcloud.teslaEV_SentryMode(self.EVid, ctrl)
        if code in ['ok']:
             self.EV_setDriver('GV21', self.command_res2ISY(res),25)
        else:
            self.EV_setDriver('GV21', self.code2ISY(code),25)
        code, res = self.TEVcloud.teslaEV_GetCarState(self.EVid)
        self.EV_setDriver('ST', self.state2ISY(res), 25)

    # needs update
    def evControlSunroof (self, command):
        logging.info(f'evControlSunroof called')
        #self.TEVcloud.teslaEV_Wake(self.EVid)
        sunroofCtrl = int(float(command.get('value')))
        res = False
        if sunroofCtrl == 1:
            code, res = self.TEVcloud.teslaEV_SunRoof(self.EVid, 'vent')
            #self.EV_setDriver()
        elif sunroofCtrl == 0:
            code, res = self.TEVcloud.teslaEV_SunRoof(self.EVid, 'close')    
        elif sunroofCtrl == 2:
            code, res = self.TEVcloud.teslaEV_SunRoof(self.EVid, 'stop')                  
        else:
            logging.error(f'Wrong command for evSunroof: {sunroofCtrl}')
            code = 'error'
        if code in ['ok']:
             self.EV_setDriver('GV21', self.command_res2ISY(res), 25)
        else:
            self.EV_setDriver('GV21', self.code2ISY(code), 25)
        code, res = self.TEVcloud.teslaEV_GetCarState(self.EVid)
        self.EV_setDriver('ST', self.state2ISY(res), 25)


    def evOpenFrunk (self, command):
        logging.info(f'evOpenFrunk called')
        #self.TEVcloud.teslaEV_Wake(self.EVid)     
        code, res = self.TEVcloud.teslaEV_TrunkFrunk(self.EVid, 'Frunk')
        logging.debug(f'Frunk result {code} - {res}')
        if code in ['ok']:
            self.EV_setDriver('GV12', 1, 25)
            self.EV_setDriver('GV21', self.command_res2ISY(res), 25)
        else:
            logging.info('Not able to send command - EV is not online')
            self.EV_setDriver('GV21', self.code2ISY(code), 25)
            self.EV_setDriver('GV12', None, 25)
        code, res = self.TEVcloud.teslaEV_GetCarState(self.EVid)
        self.EV_setDriver('ST', self.state2ISY(res), 25)


    def evOpenTrunk (self, command):
        logging.info('evOpenTrunk called')   
        code, res = self.TEVcloud.teslaEV_TrunkFrunk(self.EVid, 'Trunk')
        logging.debug(f'Trunk result {code} - {res}')
        if code in ['ok']:
            self.EV_setDriver('GV11', 1, 25)
            self.EV_setDriver('GV21', self.command_res2ISY(res), 25)    
        else:
            logging.info('Not able to send command - EV is not online')
            self.EV_setDriver('GV21', self.code2ISY(code), 25)
            self.EV_setDriver('GV11', None, 25)
        code, res = self.TEVcloud.teslaEV_GetCarState(self.EVid)
        self.EV_setDriver('ST', self.state2ISY(res), 25)


    def evHomelink (self, command):
        logging.info('evHomelink called')
        code, res = self.TEVcloud.teslaEV_HomeLink(self.EVid)
        if code in ['ok']:
             self.EV_setDriver('GV21', self.command_res2ISY(res), 25)
        else:
            self.EV_setDriver('GV21', self.code2ISY(code), 25)
        code, res = self.TEVcloud.teslaEV_GetCarState(self.EVid)
        self.EV_setDriver('ST', self.state2ISY(res), 25)



    #def updateISYdrivers(self):
    #    logging.debug('System updateISYdrivers - Controller')       
    #    value = self.TEVcloud.authenticated()
    #    self.EV_setDriver('GV0', self.bool2ISY(value), 25)
    #    #self.EV_setDriver('GV1', self.GV1, 56)
    #    self.EV_setDriver('GV2', self.distUnit, 25)
    #    self.EV_setDriver('GV3', self.tempUnit, 25)



    #def ISYupdate (self, command):
    #    logging.debug('ISY-update main node called')
    #    if self.TEVcloud.authenticated():
    #        self.longPoll()


    
    
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
        Netro =netroStart(polyglot, 'controller', 'controller', 'Tesla EV Status')

        polyglot.ready()
        polyglot.runForever()

    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
