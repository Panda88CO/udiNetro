#!/usr/bin/env python3

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)
import time
        
               
class netroSensor(udi_interface.Node):
    from  udiLib import node_queue, command_res2ISY, wait_for_node_done, tempUnitAdjust, latch2ISY, chargeState2ISY, setDriverTemp, cond2ISY,  mask2key, heartbeat, code2ISY, state2ISY, bool2ISY, online2ISY, CO_setDriver, openClose2ISY

    def __init__(self, polyglot,  primary, address, name, api):
        super(netroSensor, self).__init__(polyglot, primary, address, name)
        logging.info('_init_ Tesla ClimateNode Status Node')
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

        self.poly.ready()
        self.poly.addNode(self, conn_status = None, rename = True)
        self.wait_for_node_done()
        self.node = self.poly.getNode(address)
        self.nodeReady = True
        self.netro_api.get_info()
        logging.info('_init_ Netro Sensor NOde  COMPLETE')
        logging.debug(f'drivers ; {self.drivers}')

    def start(self):                
        logging.debug('Start TeslaEV Climate Node')  
        #self.CO_setDriver('ST', 1)
        self.nodeReady = True
        
        #self.updateISYdrivers()
        #self.update_time()
  

    def stop(self):
        logging.debug('stop - Cleaning up')
    
    #def climateNodeReady (self):
    #    return(self.nodeReady )
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


