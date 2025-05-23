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
    from  udiLib import node_queue, command_res2ISY, wait_for_node_done, tempUnitAdjust, latch2ISY, chargeState2ISY, setDriverTemp, cond2ISY,  mask2key, heartbeat, code2ISY, state2ISY, bool2ISY, online2ISY, CO_setDriver, openClose2ISY

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

        #self.updateISYdrivers()
        #self.update_time()
        #self.tempUnit = self.TEVcloud.teslaEV_GetTempUnit()

    def stop(self):
        logging.debug('stop - Cleaning up')
    
    #def climateNodeReady (self):
    #    return(self.nodeReady )
    


    def systemPoll(self):
        logging.debug('systemPoll')


    def poll(self):
        pass


    #def forceUpdateISYdrivers(self):
    #   logging.debug(f'forceUpdateISYdrivers: {self.EVid}')
    #    time.sleep(1)
    #    self.TEVcloud.teslaEV_UpdateCloudInfo(self.EVid)
    #    self.updateISYdrivers()




    def updateISYdrivers(self):
        try:

            logging.info(f'Irrigation Contrller  updateISYdrivers {self.drivers}')
            
            #self.update_time()
            self.CO_setDriver('ST', self.netro_api.get_status())

            #self.setDriverTemp('GV0', 0)
            self.CO_setDriver('GV1',len(self.netro_api.zone_list()))        
            self.setDriverTemp('GV2', 0)
            self.setDriverTemp('GV3',0)
            self.setDriverTemp('GV4',0)
          

            self.CO_setDriver('GV10', 0, 25)
            self.CO_setDriver('GV11',0, 25)

            self.CO_setDriver('GV18',0)
            self.CO_setDriver('GV19', 0)
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
            self.netro_api.set_skip_water_days(skip_days)
            #update

    def enable (self, command):
        logging.info('enable called')
        query = command.get("query")
        if 'enable.uom25' in query:
            status = int(query.get('enable.uom25'))
            self.netro_api.set_status(status)
            #Update





    id = 'irrctrl'
    commands = { 
                 'Update' : update,
                 'SkipDays' : skip_days,
                 'Enable' : enable,
                }

    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 25},   #Controller state
            {'driver': 'GV1', 'value': 0, 'uom': 72},   #Nmber of enabled zones

            {'driver': 'GV2', 'value': 99, 'uom':25}, # battery level if appropriate
            {'driver': 'GV3', 'value': 0, 'uom': 151},  #Next Start Time
            {'driver': 'GV4', 'value': 0, 'uom': 151},  #Previous End Time

            {'driver': 'GV5', 'value': 0, 'uom': 151},  #last off-line event
            {'driver': 'GV5', 'value': 0, 'uom': 151},  #last on-line event

            #{'driver': 'GV10', 'value': 0, 'uom': 25},  #Schedule Type
            #{'driver': 'GV11', 'value': 0, 'uom': 25},  #Schedule Status
            {'driver': 'GV17', 'value': 0, 'uom': 72},  #Nmber of api call remaining
            {'driver': 'GV18', 'value': 0, 'uom': 25},  #sLast event
            {'driver': 'GV19', 'value': 0, 'uom': 151}, #Last update

            ]


