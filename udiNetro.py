#!/usr/bin/env python3

import os
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

from netroAPI import netroAccess, basicAPI
from datetime import timedelta, datetime
#from tzlocal import get_localzone
from netroController import netroController
from netroSensor import netroSensor

VERSION = '0.2.4'

class netroStart(udi_interface.Node):
    from  udiLib import handleLevelChange, node_queue, command_res2ISY, code2ISY, wait_for_node_done ,  cond2ISY,  mask2key, heartbeat, state2ISY, sync_state2ISY, bool2ISY, online2ISY, CO_setDriver, openClose2ISY, apply_profile_driver_names

    def _to_base36(self, value):
        digits = '0123456789abcdefghijklmnopqrstuvwxyz'
        if value == 0:
            return '0'

        base36 = ''
        while value > 0:
            value, remainder = divmod(value, 36)
            base36 = digits[remainder] + base36
        return base36

    def _find_existing_primary_address(self, name):
        for node in self.nodes_in_db:
            if node.get('address') == 'controller':
                continue
            if node.get('primaryNode') != node.get('address'):
                continue
            if node.get('name') == name:
                return node.get('address')
        return None

    def _build_primary_address(self, name, prefix, offset=0):
        existing_address = self._find_existing_primary_address(name)
        if existing_address is not None:
            return existing_address

        timestamp_ms = int(time.time() * 1000) + offset
        return self.poly.getValidAddress(prefix + self._to_base36(timestamp_ms))

    #
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
        self.Temp_unit = 'F'
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
        polyglot.subscribe(polyglot.DISCOVER, self.discover)
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
        self.poly.ready()
        self.node = self.poly.getNode(address)
        self.customParam_done = False
        self.config_done = False

        self.serialID_list = []
        self.duplicate_keys_msg = None
        self.node_dict = {}

        logging.info('Controller init DONE')
        logging.debug(f'drivers ; {self.drivers}')

        self.poly.Notices.clear()
        assigned_primary_addresses = ['controller']
        self.poly.setCustomParamsDoc()

        while not self.customParam_done  or not self.config_done :
        #while not self.config_done and not self.portalReady :
            logging.info(f'Waiting for node to initialize {self.customParam_done} {self.config_done}')
            time.sleep(1)

        if self.duplicate_keys_msg:
            self.poly.Notices['DUPLICATE_KEYS'] = self.duplicate_keys_msg

        self.apply_profile_driver_names(self.id)
        
        logging.debug(f'Detected devices : {self.serialID_list}')

        if len(self.serialID_list) == 0:
            self.poly.Notices['SERIALID'] = 'No device API keys input in configuration folder - exiting'
            time.sleep(10)
            sys.exit()
   
        logging.debug(f'Instanciating nodes for {self.serialID_list}')
        for indx, serial_nbr in enumerate(self.serialID_list):
            logging.debug(f'Instanciating nodes for {serial_nbr}')
            api_access = basicAPI(serial_nbr)
            dev_type, name = api_access.netroType()
            del api_access
            time.sleep(1)   
            logging.debug(f'Name : {name}, {dev_type }')
            if dev_type == 'controller':
                name = self.poly.getValidName(name)
                node_address = self._build_primary_address(name, 'c', indx)
                self.node_dict[serial_nbr] = netroController(self.poly, node_address, node_address, name, serial_nbr, self.Temp_unit, self.EVENT_DAYS, self.MOIST_DAYS, self.SCH_DAYS)
                assigned_primary_addresses.append(node_address)
            elif dev_type == 'sensor':
                name = self.poly.getValidName(name)
                node_address = self._build_primary_address(name, 's', indx)
                self.node_dict[serial_nbr] = netroSensor(self.poly, node_address, node_address, name, serial_nbr, self.Temp_unit )
                assigned_primary_addresses.append(node_address)
            elif dev_type == 'error':
                self.poly.Notices[f'ERROR_{indx}'] = f'Key {serial_nbr} generated ERROR: {name}'
            else:
                self.poly.Notices[f'ERROR_{indx}'] = f'Key {serial_nbr} generated ERROR'
            time.sleep(1)

        # Wait for all instantiated nodes (and their child zone nodes) to finish initializing before loading profiles
        wait_start = time.time()
        while time.time() - wait_start < 60:
            all_ready = True
            for n in self.node_dict.values():
                if not getattr(n, 'nodeReady', False) or not getattr(n, 'system_ready', False):
                    all_ready = False
                    break
            if all_ready:
                break
            time.sleep(1)

        time.sleep(2)
        logging.debug(f'Scanning db for extra nodes : {assigned_primary_addresses}')

        if len(self.node_dict) > 0:
            for indx, node  in enumerate(self.nodes_in_db):
                #node = self.nodes_in_db[nde]
                logging.debug(f'Scanning db for unused primary nodes  : {node}')
                if node['primaryNode'] not in assigned_primary_addresses:
                    logging.debug('Removing node : {} {}'.format(node['name'], node))
                    self.poly.delNode(node['address'])
            
    
        self.update_all_drivers()
        self.nodeDefineDone = True
        self.initialized = True
        self._update_dynamic_profile()

        self.poly.Notices['done'] = 'Initialization process completed'
        time.sleep(2)
        self.poly.Notices.delete('done')




    def check_config(self):
        self.nodes_in_db = self.poly.getNodesFromDb()
        #self.config_done= True


    def configDoneHandler(self):
        logging.debug('configDoneHandler - config_done')
        # We use this to discover devices, or ask to authenticate if user has not already done so
        if not self.initialized:
            self.poly.Notices.clear()
        self.nodes_in_db = self.poly.getNodesFromDb()
        self.config_done= True
 



    def handleNotices(self, level):
        logging.info('handleNotices:')
       
    def customParamsHandler(self, userParams):
        self.customParameters.load(userParams)
        logging.debug(f'customParamsHandler called {userParams}')
        try: 
            if 'SERIALID' in userParams:
                raw_serial = str(self.customParameters['SERIALID']).strip()
                placeholders = {
                    'Input list of device API keys (space separated)',
                    'Input list of serial numbers (space separated)',
                    'Input list of serial id(s) (space separated)',
                }
                if raw_serial not in placeholders:
                    temp_list = [item for item in raw_serial.split() if item]
                    deduped_list = list(dict.fromkeys(temp_list))
                    if len(deduped_list) < len(temp_list):
                        self.duplicate_keys_msg = (
                            f'SERIALID contains {len(temp_list)} entries but only {len(deduped_list)} unique API key(s). '
                            f'Note: Netro\'s "Copy" button on their website copies the first device\'s key for every row—highlight and copy each key manually.'
                        )
                        logging.warning(self.duplicate_keys_msg)
                    else:
                        self.duplicate_keys_msg = None
                        if 'DUPLICATE_KEYS' in self.poly.Notices:
                            self.poly.Notices.delete('DUPLICATE_KEYS')
                    self.serialID_list = deduped_list
               
            else:
                logging.warning('No serialID found')
                self.customParameters['SERIALID'] = 'Input list of device API keys (space separated)'
                self.poly.Notices['SERIALID'] = 'Device API key(s) not specified'
            
            if 'EVENT_DAYS' in userParams:
                try:
                    self.EVENT_DAYS = int(self.customParameters['EVENT_DAYS'])
                except (ValueError, TypeError):
                    self.EVENT_DAYS = -5
            else:
                self.EVENT_DAYS = -5
    
            if 'SCH_DAYS' in userParams:
                try:
                    self.SCH_DAYS = int(self.customParameters['SCH_DAYS'])
                except (ValueError, TypeError):
                    self.SCH_DAYS = 7
            else:
                self.SCH_DAYS = 7

            if 'MOIST_DAYS' in userParams:
                try:
                    self.MOIST_DAYS = int(self.customParameters['MOIST_DAYS'])
                except (ValueError, TypeError):
                    self.MOIST_DAYS = -3
            else:
                self.MOIST_DAYS = -3

            if 'TEMP' in userParams:
                temp_val = str(self.customParameters['TEMP']).strip()
                if temp_val and temp_val[0] in ['c', 'C']:
                    self.Temp_unit = 'C'
                else:
                    self.Temp_unit = 'F'
            else:
                self.Temp_unit = 'F'
            logging.debug('customParamsHandler finish ')
        except Exception as e:
            logging.error(f'Error detected during custom Param parsing {e}')
        finally:
            self.customParam_done = True
        
   



    def validate_params(self):
        logging.debug('validate_params: {}'.format(self.Parameters.dump()))
        self.paramsProcessed = True


    def stop(self):
        self.Notices.clear()
        #self.background_thread.stop()
        #if self.TEV:
        #self.CO_setDriver('ST', 0, 25 )
        logging.debug('stop - Cleaning up')
        #self.scheduler.shutdown()
        self.poly.stop()
        sys.exit() # kill running threads



   


  

    def update_all_drivers(self):
        logging.debug('updateISYdrivers')


    def updateISYdrivers(self):
        
        logging.debug(f'Update main node {self.drivers}')
 

    def ISYupdate (self, command=None):
        logging.info(f'ISY-update status node  called')

    def discover(self, *args, **kwargs):
        if not (self.customParam_done and self.config_done and self.nodeDefineDone and self.initialized):
            logging.info("Discover requested - waiting for initial configuration to complete before refreshing profile")
            return
        logging.info("Discover requested - refreshing profile")
        self._update_dynamic_profile()

    def _update_dynamic_profile(self):
        if not (self.customParam_done and self.config_done and self.nodeDefineDone and self.initialized):
            logging.debug("Skipping profile update until initial configuration and node initialization are complete")
            return
        profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'profile')
        logging.info("Updating dynamic profile...")

        json_ok = False
        updater = getattr(self.poly, "updateJsonProfile", None)
        if callable(updater):
            try:
                payload = self._dynamic_profile_payload()
                updater(payload, {"waitResponse": True})
                logging.info("Dynamic JSON profile updated successfully via updateJsonProfile")
                json_ok = True
            except Exception as e:
                logging.warning(f"updateJsonProfile failed: {e}; falling back to updateProfile")

        # Fall back to static profile directory only if updateJsonProfile was unavailable or failed
        if not json_ok and os.path.isdir(profile_dir):
            try:
                if hasattr(self.poly, "updateProfile"):
                    self.poly.updateProfile()
                    logging.info("Static profile updated successfully via updateProfile")
            except Exception as e:
                logging.error(f"updateProfile failed: {e}")

    def _profile_editors(self):
        from udiLib import get_dynamic_profile_editors
        return get_dynamic_profile_editors()

    def _profile_nodedefs(self):
        from udiLib import get_dynamic_profile_nodedefs
        return get_dynamic_profile_nodedefs()

    def _profile_nls(self):
        from udiLib import get_dynamic_profile_nls
        return get_dynamic_profile_nls()

    def _dynamic_profile_payload(self):
        return {
            "delete": {
                "editors": ["*"],
                "nodedefs": ["*"],
                "linkdefs": ["*"],
            },
            "editors": self._profile_editors(),
            "nodedefs": self._profile_nodedefs(),
            "linkdefs": [],
            "nls": self._profile_nls(),
        }

    id = 'CONTROLLER'


    commands = {  }


    drivers = [
            #{'driver': 'ST', 'value': 99, 'uom': 25, 'name': 'Controller Enabled'},   #car State                       
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

        polyglot.runForever()

    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
