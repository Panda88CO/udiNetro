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
        #self.tempUnit = self.TEVcloud.teslaEV_GetTempUnit()

    def stop(self):
        logging.debug('stop - Cleaning up')
    
    #def climateNodeReady (self):
    #    return(self.nodeReady )
    

    def poll(self):
        pass
        #logging.debug(f'Climate node {self.EVid}')
        #try:
        #    if self.TEVcloud.carState != 'Offline':
        #        self.updateISYdrivers()
        #    else:
        #        logging.info('Car appears off-line/sleeping - not updating data')

        #except Exception as e:
        #    logging.error(f'Climate Poll exception : {e}')

    #def forceUpdateISYdrivers(self):
    #   logging.debug(f'forceUpdateISYdrivers: {self.EVid}')
    #    time.sleep(1)
    #    self.TEVcloud.teslaEV_UpdateCloudInfo(self.EVid)
    #    self.updateISYdrivers()

    def update_time(self):
        try:
            temp = self.TEVcloud.teslaEV_GetTimestamp(self.EVid)
            self.CO_setDriver('GV19', temp, 151)
        except ValueError:
            self.CO_setDriver('GV19', None, 25)
        '''
        try:
            temp = round(float(self.TEVcloud.teslaEV_GetTimeSinceLastStatusUpdate(self.EVid)/60), 0)
            self.CO_setDriver('GV20', temp, 44)
        except ValueError:
            self.CO_setDriver('GV20', None, 25)
        '''

    def updateISYdrivers(self):
        try:

            logging.info(f'Climate updateISYdrivers {self.EVid}: {self.drivers}')
            
            self.update_time()
            self.setDriverTemp('ST', self.TEVcloud.teslaEV_GetCabinTemp(self.EVid))
            self.setDriverTemp('GV2', self.TEVcloud.teslaEV_GetOutdoorTemp(self.EVid))
            self.setDriverTemp('GV3', self.TEVcloud.teslaEV_GetLeftTemp(self.EVid))
            self.setDriverTemp('GV4', self.TEVcloud.teslaEV_GetRightTemp(self.EVid))
                

            
            #self.setDriverTemp('GV12', self.TEVcloud.teslaEV_MaxCabinTempCtrl(self.EVid))
            #self.setDriverTemp('GV13', self.TEVcloud.teslaEV_MinCabinTempCtrl(self.EVid))
            
            self.CO_setDriver('GV14', self.bool2ISY(self.TEVcloud.teslaEV_SteeringWheelHeatOn(self.EVid)), 25) #need to be implemented        
        except Exception as e:
            logging.error(f'updateISYdrivers climate node  failed: Nodes may not be 100% ready {e}')


    #def ISYupdate (self, command):
    #    logging.info('ISY-update called')
        #super(teslaEV_ClimateNode, self).ISYupdate()
        #code, state = self.TEVcloud.teslaEV_update_connection_status(self.EVid)
        #code, res = self.TEVcloud.teslaEV_UpdateCloudInfo(self.EVid)
        #super(teslaEV_ClimateNode, self).update_all_drivers(code)
        #super(teslaEV_ClimateNode, self).display_update()
        #self.CO_setDriver('GV21', self.command_res2ISY(code), 25)

    def node_ready(self):
        return(self.nodeReady)



    def ISYupdate (self, command):
        logging.info('evSetSeat5Heat called') 
        seatTemp = int(command.get('value'))  
        code, res = self.TEVcloud.teslaEV_SetSeatHeating(self.EVid, 5, seatTemp)
                
        if code in ['ok']:
            self.CO_setDriver('GV21', self.command_res2ISY(res), 25)
            self.CO_setDriver('GV9', seatTemp, 25)
        else:
            logging.info('Not able to send command - EV is not online')
            self.CO_setDriver('GV21', self.code2ISY(code), 25)
            self.CO_setDriver('GV9', None, 25)            


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


