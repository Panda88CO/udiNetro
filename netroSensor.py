#!/usr/bin/env python3

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)
import time
from netroAPI import netroAccess
               
class netroSensor(udi_interface.Node):
    from  udiLib import node_queue, command_res2ISY, wait_for_node_done,cond2ISY,  mask2key, heartbeat, code2ISY, state2ISY, bool2ISY, online2ISY, CO_setDriver

    def __init__(self, polyglot,  primary, address, name):
        super(netroSensor, self).__init__(polyglot, primary, address, name)
        logging.info('_init_ TNetro Sensor Node')
        self.poly = polyglot
        self.ISYforced = False
        self.serial_id = address
        self.primary = primary
        self.address = address
        self.name = name
        self.nodeReady = False
        #self.node = self.poly.getNode(address)
        self.n_queue = []
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(polyglot.POLL, self.systemPoll)
        self.poly.ready()
        self.poly.addNode(self, conn_status = None, rename = True)
        self.wait_for_node_done()
        self.node = self.poly.getNode(address)
        self.nodeReady = True
        self.netro_api.get_info()
        logging.info('_init_ Netro Sensor Node  COMPLETE')
        logging.debug(f'drivers ; {self.drivers}')
        self.sensor_data = None

    def start(self):                
        logging.debug('Start Netro Sensor Node')  

        #self.CO_setDriver('ST', 1)
        self.netro_api = netroAccess(self.serial_id)
        self.zone_nodes = {}
        zone_addresses = [self.primary]


        self.nodeReady = True
        self.sensor_data = self.netro_api.update_sensor_data()
        self.updateISYdrivers()
        
        logging.debug(f'Scanning db for extra nodes : {self.nodes_in_db}')
        

            
    def stop(self):
        logging.debug('stop - Cleaning up')


    def stop(self):
        logging.debug('stop - Cleaning up')

    def retrieve_sensor_data(self):
        self.sensor_data = self.netro_api.update_sensor_data()
        self.updateISYdrivers()

    def ISYupdate (self, command):
        logging.info('ISY-update called')
        self.retrieve_sensor_data()

    def systemPoll(self, pollList):
        logging.debug(f'systemPoll - {pollList}')
    
        if 'longPoll' in pollList: 
            self.poll()
            if 'shortPoll' in pollList: #send short polls heart beat as shortpoll is not executed
                self.poll()
        if 'shortPoll' in pollList:
            self.poll()

    def poll(self):
        self.netro_api.update_sensor_data()
        self.updateISYdrivers()
        self.sensor_data = self.retrieve_sensor_data()
   

    def updateISYdrivers(self):
        logging.debug(f'updateISYdrivers {self.sensor_data}')
        self.CO_setDriver('ST', self.sensor_data['moisture'])
        self.CO_setDriver('TEMP', self.sensor_data['temperature'])
        self.CO_setDriver('GV2', self.sensor_data['temperature'])
        self.CO_setDriver('GV14', self.sensor_data['temperature'])
        self.CO_setDriver('GV15', self.sensor_data['temperature'])
    id = 'sensor'
    commands = { 'UPDATE' : ISYupdate, 
              
                }

    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 70},  #Moisture 0-100
            {'driver': 'TEMP', 'value': 0, 'uom': 4},  #outside_temp
            {'driver': 'GV2', 'value': 0, 'uom': 36},  #sunlight (LUX)
            {'driver': 'GV14', 'value': 0, 'uom': 51},  #battery
            {'driver': 'GV15', 'value': 0, 'uom': 25},  #con status
            ]


