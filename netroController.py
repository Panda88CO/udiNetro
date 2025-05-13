#!/usr/bin/env python3

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)
import time
        
               
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

        self.poly.ready()
        self.poly.addNode(self, conn_status = None, rename = True)
        self.wait_for_node_done()
        self.node = self.poly.getNode(address)
        self.nodeReady = True
        logging.info('_init_ Tesla ClimateNode Status Node COMPLETE')
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


    def updateISYdrivers(self):
        try:

            logging.info(f'Irrigation Contrller  updateISYdrivers {self.EVid}: {self.drivers}')
            
            self.update_time()
            self.setDriverTemp('ST', 0)

            self.setDriverTemp('GV0', 0)
            self.setDriverTemp('GV1',0)        
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
        #super(teslaEV_ClimateNode, self).ISYupdate()
        #code, state = self.TEVcloud.teslaEV_update_connection_status(self.EVid)
        #code, res = self.TEVcloud.teslaEV_UpdateCloudInfo(self.EVid)
        #super(teslaEV_ClimateNode, self).update_all_drivers(code)
        #super(teslaEV_ClimateNode, self).display_update()
        #self.CO_setDriver('GV21', self.command_res2ISY(code), 25)

    def node_ready(self):
        return(self.nodeReady)

    def update (self, command):
        logging.info('update- called')





    def water_control (self, command):
        logging.info('water_control called') 
        driverTemp = None
        passengerTemp = None
        query = command.get("query")
        if 'driver.uom4' in query:
            driverTemp = int(query.get('driver.uom4'))
        elif 'driver.uom17' in query:
            driverTemp = int((int(query.get('driver.uom17'))-32)*5/9)
        if 'passenger.uom4' in query:
            passengerTemp = int(query.get('passenger.uom4'))  
        elif 'passenger.uom17' in query:
            passengerTemp = int((int(query.get('passenger.uom17'))-32)*5/9)
        code, res = self.TEVcloud.teslaEV_SetCabinTemps(self.EVid, driverTemp, passengerTemp)
        if code in ['ok']:
            self.CO_setDriver('GV21', self.command_res2ISY(res), 25)
            self.setDriverTemp( 'GV3', driverTemp )
            self.setDriverTemp( 'GV4', passengerTemp)
        else:
            logging.info('Not able to send command - EV is not online')
            self.CO_setDriver('GV21', self.code2ISY(code), 25)
            self.CO_setDriver('GV3', None, 25)
            self.CO_setDriver('GV4', None, 25)


    def skip_days (self, command):
        logging.info('skip_days called')
  
      

    def enable (self, command):
        logging.info('enable called')



    id = 'irr_ctrl'
    commands = { 
                 'Update' : update,
                 'Water' : water_control,
                 'SkipDays' : skip_days,
                 'Enable' : enable,
                }

    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 25},  #Irrigation state
            #{'driver': 'GV0', 'value': 0, 'uom': 25},  #Irrigation state
            {'driver': 'GV1', 'value': 0, 'uom': 0},  #Nmber of enabled zones
            {'driver': 'GV2', 'value': 0, 'uom': 151},  #Next Start Time
            {'driver': 'GV3', 'value': 0, 'uom': 151},  #Previous Start Time
            {'driver': 'GV4', 'value': 0, 'uom': 151},  #Previous End Time
            {'driver': 'GV10', 'value': 0, 'uom': 25},  #Schedule Type
            {'driver': 'GV11', 'value': 0, 'uom': 25},  #Schedule Status
            {'driver': 'GV18', 'value': 0, 'uom': 25},  #sLast event
            {'driver': 'GV19', 'value': 0, 'uom': 151},  #Last update

            ]


