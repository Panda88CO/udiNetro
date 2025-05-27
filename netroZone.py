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
    from  udiLib import zoneconfig2ISY, node_queue, command_res2ISY, wait_for_node_done, tempUnitAdjust, latch2ISY, chargeState2ISY, setDriverTemp, cond2ISY,  mask2key, heartbeat, code2ISY, state2ISY, bool2ISY, online2ISY, CO_setDriver, openClose2ISY

    def __init__(self, polyglot,  primary, address, name, api):
        super(netroZone, self).__init__(polyglot, primary, address, name)
        logging.info(f'_init_ Netro Irrigation Zone node {primary} {address} {name}')
        self.poly = polyglot

        self.netro_api = api
        self.primary = primary
        self.address = address
        self.name = name
        match = re.search(r'zo\d+', self.address )
        logging.debug(f'Zone number match {match}')

        self.zone_nbr = int(match.group(0)) if match else -1

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

   
    def updateISYdrivers(self):
        try:

            logging.info(f'Irrigation Contrller  updateISYdrivers {self.zone_nbr}: {self.drivers}')
            
           #self.update_time()
            self.CO_setDriver('ST', self.netro_api.zone_status(self.zone_nbr))
            self.CO_setDriver('GV0', self.zone_nbr)

            self.CO_setDriver('GV1',self.zoneconfig2ISY(self.netro_api.zone_config(self.zone_nbr)))        
            self.setDriverTemp('GV2', self.netro_api.moisture(self.zone_nbr) )
            self.setDriverTemp('GV3', self.netro_api.moisture_slope(self.zone_nbr) )
            self.setDriverTemp('GV4', self.netro_api.last_sch_start(self.zone_nbr))
            self.setDriverTemp('GV5', self.netro_api.last_sch_end(self.zone_nbr))
            self.setDriverTemp('GV6', self.netro_api.next_sch_start(self.zone_nbr))
            self.setDriverTemp('GV7', self.netro_api.next_sch_end(self.zone_nbr))
          

            #self.CO_setDriver('GV10', 0, 25)
            #self.CO_setDriver('GV11',0, 25)

            #self.CO_setDriver('GV18',0)
            self.CO_setDriver('GV19',self.netro_api.api_last_update() )
        except Exception as e:
            logging.error(f'updateISYdrivers Netro Irrigation Controller  failed: Nodes may not be 100% ready {e}')


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
            {'driver': 'GV2', 'value': 0, 'uom': 72},  #Moisture
            {'driver': 'GV3', 'value': 0, 'uom': 72},  #moisture slope 
            {'driver': 'GV4', 'value': 0, 'uom': 151},  #Previous End Time
            {'driver': 'GV5', 'value': 0, 'uom': 151},  #Previous End Time
            {'driver': 'GV6', 'value': 0, 'uom': 151},  #Previous End Time
            {'driver': 'GV7', 'value': 0, 'uom': 151},  #Previous End Time
            #{'driver': 'GV10', 'value': 0, 'uom': 25},  #Schedule Type
            #{'driver': 'GV11', 'value': 0, 'uom': 25},  #Schedule Status
            #{'driver': 'GV18', 'value': 0, 'uom': 25},  #sLast event
            {'driver': 'GV19', 'value': 0, 'uom': 151},  #Last update

            ]


