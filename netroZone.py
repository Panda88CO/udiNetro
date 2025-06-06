#!/usr/bin/env python3

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)
import time
import re        
               
class netroZone(udi_interface.Node):
    from  udiLib import zoneconfig2ISY, ctrl_status2ISY, node_queue, command_res2ISY, wait_for_node_done, cond2ISY,  mask2key, heartbeat, code2ISY, state2ISY, bool2ISY, online2ISY, CO_setDriver

    def __init__(self, polyglot,  primary, address, name, api):
        super(netroZone, self).__init__(polyglot, primary, address, name)
        logging.info(f'_init_ Netro Irrigation Zone node {primary} {address} {name}')
        self.poly = polyglot

        self.netro_api = api
        self.primary = primary
        self.address = address
        self.name = name
        match = re.search(r"_z(\d+)", self.address )
        #logging.debug(f'Zone number match {match}')

        self.zone_nbr = int(match.group(1)) if match else -1
        logging.debug(f'Zone number extracted {self.zone_nbr}')
        self.nodeReady = False
        #self.node = self.poly.getNode(address)
        self.n_queue = []
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.poly.subscribe(self.poly.START, self.start, address)

        self.poly.ready()
        self.poly.addNode(self, conn_status = None, rename = True)
        self.wait_for_node_done()
        self.node = self.poly.getNode(address)
        self.nodeReady = True
        logging.info('_init_ Netro Irrigation Controlle Node COMPLETE')
        logging.debug(f'drivers ; {self.drivers}')

    def start(self):                
        logging.debug(f'Start Netro Irrigation Controller Node {self.zone_nbr}') 

        #self.CO_setDriver('ST', 1)
        self.nodeReady = True
        self.updateISYdrivers()
        #self.update_time()
  

    def stop(self):
        logging.debug('stop - Cleaning up')
    

   
    def updateISYdrivers(self):
        try:

            logging.info(f'Irrigation Contrller  updateISYdrivers {self.zone_nbr}: {self.drivers}')
            
           #self.update_time()
            logging.debug(f'Zone {self.zone_nbr} {self.netro_api.zone_status(self.zone_nbr)}')
            self.CO_setDriver('ST', self.ctrl_status2ISY(self.netro_api.zone_status(self.zone_nbr)))
            self.CO_setDriver('GV0', self.zone_nbr)

            self.CO_setDriver('GV1',self.zoneconfig2ISY(self.netro_api.zone_config(self.zone_nbr)))        
            self.CO_setDriver('GV2', self.netro_api.moisture(self.zone_nbr) )
            self.CO_setDriver('GV3', self.netro_api.moisture_slope(self.zone_nbr) )
            if self.netro_api.zone_config(self.zone_nbr) in ['ASSISTANT', 'TIMER']:
                self.CO_setDriver('GV4', self.netro_api.last_sch_start(self.zone_nbr), 151)
                self.CO_setDriver('GV5', self.netro_api.last_sch_end(self.zone_nbr), 151)
                self.CO_setDriver('GV6', self.netro_api.next_sch_start(self.zone_nbr), 151)
                self.CO_setDriver('GV7', self.netro_api.next_sch_end(self.zone_nbr), 151)
            else:
                self.CO_setDriver('GV4', 98, 25)
                self.CO_setDriver('GV5', 98, 25)
                self.CO_setDriver('GV6', 98, 25)
                self.CO_setDriver('GV7', 98, 25)

            #self.CO_setDriver('GV10', 0, 25)
            #self.CO_setDriver('GV11',0, 25)

            #self.CO_setDriver('GV18',0)
            self.CO_setDriver('GV19',self.netro_api.api_last_update() )
        except Exception as e:
            logging.error(f'updateISYdrivers Netro Irrigation Controller  failed: Nodes may not be 100% ready {e}')


    def ISYupdate (self, command):
        logging.info('ISY-update called')


    def node_ready(self):
        return(self.nodeReady)

    def update (self, command):
        logging.info('update- called')





    def water_control (self, command):
        logging.info('water_control called') 
        duration = 0
        delay=0

        query = command.get("query")
        if 'Duration.uom44' in query:
            duration = int(query.get('Duration.uom44'))
        if 'Delay.uom44' in query:
            delay = int(query.get('Delay.uom44'))  
     
        status = self.netro_api.set_watering(duration, delay, self.zone_nbr)    
        logging.debug(f'set_watering {status}')





    id = 'zone'
    commands = { 
                 'Update' : update,
                 'Water' : water_control,
                 #'SkipDays' : skip_days,
                 #'Enable' : enable,
                }

    drivers = [
            {'driver': 'ST', 'value': 99, 'uom': 25},  #Zone Status
            {'driver': 'GV0', 'value': 0, 'uom': 0},  #Zone Number
            {'driver': 'GV1', 'value': 99, 'uom': 25},  #Zone config
            {'driver': 'GV2', 'value': 0, 'uom': 70},  #Moisture
            {'driver': 'GV3', 'value': 0, 'uom': 70},  #moisture slope 
            {'driver': 'GV4', 'value': 0, 'uom': 151},  #Previous Start Time
            {'driver': 'GV5', 'value': 0, 'uom': 151},  #Previous End Time
            {'driver': 'GV6', 'value': 0, 'uom': 151},  #Next Start Time
            {'driver': 'GV7', 'value': 0, 'uom': 151},  #Next End Time
            #{'driver': 'GV10', 'value': 0, 'uom': 25},  #Schedule Type
            #{'driver': 'GV11', 'value': 0, 'uom': 25},  #Schedule Status
            #{'driver': 'GV18', 'value': 0, 'uom': 25},  #sLast event
            {'driver': 'GV19', 'value': 0, 'uom': 151},  #Last update

            ]


