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
        logging.info('_init_ Tesla ClimateNode Status Node')
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
        logging.info('_init_ Netro Sensor NOde  COMPLETE')
        logging.debug(f'drivers ; {self.drivers}')

    def start(self):                
        logging.debug('Start Netro Sensor Node')  

        #self.CO_setDriver('ST', 1)
        self.netro_api = netroAccess(self.serial_id)
        self.zone_nodes = {}
        zone_addresses = [self.primary]


        self.nodeReady = True
        self.netro_api.update_sensor_data()
        self.updateISYdrivers()
        
        logging.debug(f'Scanning db for extra nodes : {self.nodes_in_db}')
        

        for indx, node  in enumerate(self.nodes_in_db):
            logging.debug(f'Scanning db for node : {node}')
            if node['primaryNode']  in self.serial_id and node['address'] not in zone_addresses:
                logging.debug('Removing node : {} {}'.format(node['name'], node))
                self.poly.delNode(node['address'])
        self.system_ready = True
            
    def stop(self):
        logging.debug('stop - Cleaning up')


    def stop(self):
        logging.debug('stop - Cleaning up')

    def ISYupdate (self, command):
        logging.info('ISY-update called')

    def poll(self):
        pass
   



    id = 'sensor'
    commands = { 'UPDATE' : ISYupdate, 
              
                }

    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 4},  #inside_temp
            {'driver': 'GV2', 'value': 0, 'uom': 4},  #outside_temp
            {'driver': 'GV3', 'value': 0, 'uom': 4},  #driver_temp_setting
            {'driver': 'GV4', 'value': 0, 'uom': 4},  #passenger_temp_setting
            {'driver': 'GV5', 'value': 0, 'uom': 25},  #seat_heater_left
            {'driver': 'GV6', 'value': 0, 'uom': 25},  #seat_heater_right
            {'driver': 'GV7', 'value': 0, 'uom': 25},  #seat_heater_rear_left
            {'driver': 'GV8', 'value': 0, 'uom': 25},  #seat_heater_rear_center
            {'driver': 'GV9', 'value': 0, 'uom': 25},  #seat_heater_rear_right
            {'driver': 'GV15', 'value': 0, 'uom': 25},  #seat_heater_third_left
            {'driver': 'GV16', 'value': 0, 'uom': 25},  #seat_heater_third_right
            {'driver': 'GV10', 'value': 0, 'uom': 25}, #is_preconditioning
            {'driver': 'GV11', 'value': 0, 'uom': 25}, #is_preconditioning
            {'driver': 'GV14', 'value': 99, 'uom': 25}, #Steering Wheel Heat
            {'driver': 'GV19', 'value': 0, 'uom': 151},  #Last combined update Hours           
            {'driver': 'GV21', 'value': 99, 'uom': 25}, #Last Command status
            ]


