#!/usr/bin/env python3

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)
import time
from netroZone import netroZone
               
class netroController(udi_interface.Node):
    from  udiLib import node_queue, heartbeat, ctrl_status2ISY, command_res2ISY, wait_for_node_done, cond2ISY,  mask2key, heartbeat, code2ISY, state2ISY, bool2ISY, online2ISY, CO_setDriver

    def __init__(self, polyglot,  primary, address, name, api):
        super(netroController, self).__init__(polyglot, primary, address, name)
        logging.info('_init_ Netro Irrigation Controller node')
        self.poly = polyglot
  
        self.ISYforced = False
        self.netro_api = api
        self.primary = primary
        self.address = address
        self.name = name
        self.nodeReady = False
        #self.node = self.poly.getNode(address)
        self.n_queue = []
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.poly.subscribe(self.poly.START, self.start, address)
        #polyglot.subscribe(polyglot.LOGLEVEL, self.handleLevelChange)
        #polyglot.subscribe(polyglot.NOTICES, self.handleNotices)
        polyglot.subscribe(polyglot.POLL, self.systemPoll)
        self.poly.ready()
        self.poly.addNode(self, conn_status = None, rename = True)
        self.wait_for_node_done()
        self.node = self.poly.getNode(address)
        self.nodeReady = True
        logging.info('_init_ Netro Irrigation Controller Node COMPLETE')
        logging.debug(f'drivers ; {self.drivers}')
        

    def start(self):                
        logging.debug('Start Netro Irrigation Node')  
        #self.CO_setDriver('ST', 1)
        self.zone_nodes = {}
        active_zones = self.netro_api.zone_list()
        logging.debug(f'Adding   {len(active_zones)} {active_zones}')
        for key, tmp_zone in active_zones.items():
            logging.debug(f'Key {key} Selected Zone {tmp_zone}')
            name = self.poly.getValidName(tmp_zone['name'])

            address = self.poly.getValidAddress(self.address[-10:]+'_z'+str(key))
            self.zone_nodes[tmp_zone['ith']] = netroZone(self.poly, self.address, address, name , self.netro_api )
        self.nodeReady = True
        self.netro_api.update_controller_data()
        self.updateISYdrivers()
        #self.update_time()
    

    def stop(self):
        logging.debug('stop - Cleaning up')
    
    #def climateNodeReady (self):
    #    return(self.nodeReady )
    


    def systemPoll(self, pollList):
        logging.debug(f'systemPoll - {pollList}')
    
        if 'longPoll' in pollList: 
            self.longPoll()
            if 'shortPoll' in pollList: #send short polls heart beat as shortpoll is not executed
                self.heartbeat()
        if 'shortPoll' in pollList:
            self.shortPoll()


    def longPoll(self):
        pass


    def shortPoll(self):
        pass


    #def forceUpdateISYdrivers(self):




    def updateISYdrivers(self):
        try:

            logging.info(f'Irrigation Contrller  updateISYdrivers')
            
            #self.update_time()
            self.CO_setDriver('ST', self.ctrl_status2ISY(self.netro_api.status()))

            #self.setDriverTemp('GV0', 0)
            self.CO_setDriver('GV1',len(self.netro_api.zone_list()))        
            #elf.setDriverTemp('GV2', 0)
            self.CO_setDriver('GV3',self.netro_api.last_end_time())
            self.CO_setDriver('GV4',self.netro_api.next_start_time())
            self.CO_setDriver('GV5',self.netro_api.last_offline_event())
            self.CO_setDriver('GV6',self.netro_api.last_online_event())                  
            self.CO_setDriver('GV16', self.netro_api.get_battery_level())
            self.CO_setDriver('GV10', 0, 25)
            self.CO_setDriver('GV11',0, 25)
            self.CO_setDriver('GV17', self.netro_api.apicalls_reamaining())
            #self.CO_setDriver('GV18',0)
            self.CO_setDriver('GV19', self.netro_api.last_API)
        except Exception as e:
            logging.error(f'updateISYdrivers climate node  failed: Nodes may not be 100% ready {e}')


    #def ISYupdate (self, command):
    #    logging.info('ISY-update called')


    def node_ready(self):
        return(self.nodeReady)

    def update (self, command):
        logging.info('update- called')



    def skip_days (self, command):
        logging.info('skip_days called')
        query = command.get("query")
        if 'SkipDays.uom10' in query:
            skip_days = int(query.get('SkipDays.uom10'))
            res = self.netro_api.set_skip_water_days(skip_days)
            if res == 'ok':
                time.sleep(2)
                self.netro_api.update_schedules()
                self.updateISYdrivers()

    def enable (self, command):
        logging.info('enable called')
        query = command.get("query")
        if 'enable.uom25' in query:
            status = int(query.get('enable.uom25'))
            res = self.netro_api.set_status(status)
            if res == 'ok':
                time.sleep(1)
                self.CO_setDriver('ST', self.netro_api.get_status())

    def stop_water (self, command=None):
        logging.info('stop_water called')
        res = self.netro_api.stop_watering()
        time.sleep(1)
        if res == 'ok':
            time.sleep(2)
            self.netro_api.update_events()
            self.netro_api.update_schedules()
            self.updateISYdrivers()


    id = 'irrctrl'
    commands = { 
                 'Update' : update,
                 'SkipDays' : skip_days,
                 'Enable' : enable,
                 'StopWater' : stop_water,
                }

    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 25},   #Controller state
            {'driver': 'GV1', 'value': 0, 'uom': 72},   #Nmber of enabled zones

            #{'driver': 'GV2', 'value': 99, 'uom':25}, # battery level if appropriate
            {'driver': 'GV3', 'value': 0, 'uom': 151},  #Next Start Time
            {'driver': 'GV4', 'value': 0, 'uom': 151},  #Previous End Time

            {'driver': 'GV5', 'value': 99, 'uom': 25},  #last off-line event
            {'driver': 'GV6', 'value': 0, 'uom': 151},  #last on-line event


            #{'driver': 'GV10', 'value': 0, 'uom': 25},  #Schedule Type
            #{'driver': 'GV11', 'value': 0, 'uom': 25},  #Schedule Status
            {'driver': 'GV16', 'value': 99, 'uom':25}, # battery level if appropriate
            {'driver': 'GV17', 'value': 0, 'uom': 72},  #Nmber of api call remaining
            #{'driver': 'GV18', 'value': 0, 'uom': 25},  #sLast event
            {'driver': 'GV19', 'value': 0, 'uom': 151}, #Last update

            ]


