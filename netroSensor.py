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
    from  udiLib import node_queue, command_res2ISY, ctrl_status2ISY, wait_for_node_done,cond2ISY,  mask2key, heartbeat, code2ISY, state2ISY, bool2ISY, online2ISY, CO_setDriver

    def __init__(self, polyglot,  primary, address, name, temp_unit):
        super(netroSensor, self).__init__(polyglot, primary, address, name)
        logging.info('_init_ Netro Sensor Node')
        self.poly = polyglot
        self.ISYforced = False
        self.serial_id = address
        self.primary = primary
        self.address = address
        self.name = name
        self.temp_unit = temp_unit
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
        
        logging.info('_init_ Netro Sensor Node  COMPLETE')
        logging.debug(f'drivers ; {self.drivers}')
        self.sensor_data = None

    def start(self):                
        logging.debug('Start Netro Sensor Node')  
        while not self.nodeReady:
            time.sleep(1)
        #self.CO_setDriver('ST' , 1)
        self.netro_api = netroAccess(self.serial_id)
        #self.netro_api.get_info()
        #self.zone_nodes = {}
        #zone_addresses = [self.primary]
        self.nodeReady = True
        self.sensor_data = self.netro_api.update_sensor_data()
        self.updateISYdrivers()

        

            
    def stop(self):
        logging.debug('stop - Cleaning up')


    def stop(self):
        logging.debug('stop - Cleaning up')

    def retrieve_sensor_data(self):
        self.sensor_data = self.netro_api.update_sensor_data()
        self.updateISYdrivers()

    def ISYupdate (self, command):
        logging.info('ISY-update called')
        self.sensor_data = self.retrieve_sensor_data()

    def systemPoll(self, pollList):
        logging.debug(f'systemPoll - {pollList}')
    
        if 'longPoll' in pollList: 
            self.longpoll()
            if 'shortPoll' in pollList: #send short polls heart beat as shortpoll is not executed
                self.shortpoll()
        if 'shortPoll' in pollList:
            self.shortpoll()

    def longpoll(self):
        self.netro_api.update_info()
        self.updateISYdrivers()

    def shortpoll(self):
        self.netro_api.update_sensor_data()
        self.updateISYdrivers()

    def updateISYdrivers(self):
        logging.debug(f'updateISYdrivers')
        if self.sensor_data is not None:
            self.CO_setDriver('ST', self.netro_api.get_sensor_data('moisture'),72)
            if self.temp_unit == 'C':
                self.CO_setDriver('TEMP', round(self.netro_api.get_sensor_data('celsius'),1), 4)
            else:
                self.CO_setDriver('TEMP', round(self.netro_api.get_sensor_data('fahrenheit'),1), 17)
            self.CO_setDriver('GV2', self.netro_api.get_sensor_data('sunlight'),36)
            self.CO_setDriver('GV14', self.netro_api.get_sensor_data('battery_level'), 51)
            self.CO_setDriver('GV15', self.ctrl_status2ISY(self.netro_api.get_sensor_data('status')),25)
            self.CO_setDriver('GV18', self.netro_api.get_sensor_data('time'),151)    
            self.CO_setDriver('GV19', self.netro_api.last_API(), 151)

    id = 'sensor'
    commands = { 'UPDATE' : ISYupdate, 
              
                }

    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 72},  #Moisture 0-100
            {'driver': 'TEMP', 'value': 0, 'uom': 4},  #outside_temp
            {'driver': 'GV2', 'value': 0, 'uom': 36},  #sunlight (LUX)
            {'driver': 'GV18', 'value': 0, 'uom': 151}, # data report time 
            {'driver': 'GV14', 'value': 0, 'uom': 51},  #battery
            {'driver': 'GV15', 'value': 0, 'uom': 25},  #con status
            {'driver': 'GV19', 'value': 0, 'uom': 151}, #Last update
            ]


