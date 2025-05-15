#!/usr/bin/env python3
import requests
import time
import json
from threading import Lock
from datetime import timedelta, datetime, timezone
#from tzlocal import get_localzone

try:
    #import udi_interface
    from udi_interface import LOGGER
    logging = LOGGER
#    ISY = udi_interface.ISY
except ImportError:
    import logging
    logging.basicConfig(level=30)


STATUS_CODE = {'STANDBY':0, 'SETUP':1, 'ONLINE':2, 'WATERING':3, 'OFFLINE':4, 'SLEEPING':5, 'POWEROFF':6}

class netroAccess(object):
    def __init__(self,  serial_nbr):
        #super().__init__(polyglot)
        logging.info(f'Netro API initializing')
        #self.poly = polyglot
        self.serialID = serial_nbr
        self.yourApiEndpoint = 'https://api.netrohome.com/npa/v1'
        self.netro= {}
        self.device_type = ''
        #self.tz = get_localzone()
        self.get_info()





    def get_device_type(self) -> str:
        return(self.device_type)

    def get_status(self):
        logging.debug('get_status')
        try:
            return(STATUS_CODE[self.netro['info']['status']])
        except KeyError as e:
            logging.error('ERROR - no key found {e}')
            return(None)
    
    
    def get_zone_list(self):
        logging.debug('get_zone_list')
        return(self.netro['active_zone_list'])

    def get_zone_info(self, zone_nbr=None):
        try:
            logging.debuf('get_device_name')

            if self.device_type == 'controller':
                return(self.netro['active_zone_list'][zone_nbr])
                                            
        except KeyError as e:
            logging.error(f'Error: get_zone_info {e}')
            return(None)
        

    def get_device_name(self):
        try:
            logging.debug('get_device_name')
            if self.device_type == 'controller':
                return(self.netro['info']['device']['name'])
            elif self.device_type == 'sensor':
               return('sensor'+str(self.serialID))
            
            else:
                return('Unknown')
        except KeyError as e:
            logging.error(f'Error: get_device_name {e}')
            return(None)
        

    def get_info(self) -> str:
        try:
            logging.debug(f'get info {self.serialID}')
            status, res = self._callApi('GET', '/info.json')

            if status == 'ok':
                logging.debug('res = {}'.format(res['data']))                
                #self.netro_info['info'] = res['data'] #NOT CORRECT
                date_time_str = res['meta']['last_active']#+'GMT-00:00'
                date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M:%S')
                date_time_obj = date_time_obj.replace(tzinfo=timezone.utc)
                unix_time = int(date_time_obj.timestamp())
                self.netro['last_api_time'] = unix_time  
                if 'device' in res['data']: # controller
                    self.device_type = 'controller'
                    self.netro['info'] = res['data'] 
                    self.netro['active_zone_list'] = []
                    for indx, zone in enumerate( self.netro['info']['device']['zones']):
                        if zone['enabled']:
                            self.netro['active_zone_list'].append(zone)
                elif 'sensor_data' in res['data']: #sensor
                    self.device_type ='sensor'
                    self.netro['info'] = res['data']
                logging.debug(f'self.netro {self.netro}')
                return(status)
            else:
                return(None)
        except Exception as e:
            logging.debug(f'Exception get_info {self.serialID} {e} ')
            return(None)
        

    def get_moisture(self, zone_list=None ) -> dict:
        try:
            logging.debug(f'get_moisture {self.serialID}')
            params = {}
            params['zones'] = zone_list 
            status, res = self._callApi('GET', '/moistures.json', params)
            if status == 'ok':
                logging.debug(f'res = {res}')                
                if zone_list is None: # all zones are updated
                    logging.debug('all zones')
                return(res)
            else:
                return(None)
        except Exception as e:
            logging.debug(f'Exception get_moisture {self.serialID} {e} ')
            return(None)
        

    def get_schedules(self, zone_list=None ) -> dict:
        try:
            logging.debug(f'get_schedules {self.serialID}')
            params = {}
            if zone_list is not None:
                params['zones'] = zone_list 
            status, res = self._callApi('GET', '/schedules.json', params)
            logging.debug(f'status = {status}  res = {res} ')
            return(res)

        except Exception as e:
            logging.debug(f'Exception get_schedules {self.serialID} {e} ')
            return(None)
        
    def get_events(self, zone_list=None ) -> dict:
        try:
            logging.debug(f'get_events {self.serialID}')
            params = {}
            if zone_list is not None:
                params['zones'] = zone_list 
            status, res = self._callApi('GET', '/events.json', params)
            if status == 'ok':
                logging.debug(f'res = {res}')
                return(res)
            else:
                return(None)
        except Exception as e:
            logging.debug(f'Exception get_events {self.serialID} {e} ')
            return(None)
        
    
    
    def set_status(self, status=None):
        try:
            logging.debug(f'set_status {self.serialID}')
            params = {'key':str(self.serialID)}
            if status is not None:

                params['status'] = int(status) 
                status, res = self._callApi('POST', '/set_status.json', params)
                if status == 'ok':
                    logging.debug(f'res = {res}')
                    return(res)
                else:
                    return(None)
            return(None)
        except Exception as e:
            logging.debug(f'Exception set_status {self.serialID} {e} ')
            return(None)
        
    def set_watering(self, duration=1, delay=0, zone_list = None):
        try:
            logging.debug(f'set_watering {self.serialID} {duration} {delay} {zone_list}')
            params = {'key':str(self.serialID),
                      'duration':int(duration)}
            if delay != 0:
                params['delay']=int(delay)
            if zone_list is not None and type(zone_list) is list:
                params['zones'] = int(zone_list) 
            status, res = self._callApi('POST', '/water.json', params)
            if status == 'ok':
                logging.debug(f'res = {res}')
                return(res)
            else:
                return(None)
        except Exception as e:
            logging.debug(f'Exception set_status {self.serialID} {e} ')
            return(None)

    def stop_watering(self):
        try:
            logging.debug(f'stop_watering {self.serialID} ')
            params = {'key':str(self.serialID)}
            status, res = self._callApi('POST', '/stop_water.json', params)
            if status == 'ok':
                logging.debug(f'res = {res}')
                return(res)
            else:
                return(None)
        except Exception as e:
            logging.debug(f'Exception stop_watering {self.serialID} {e} ')
            return(None)
        
    def set_no_water_days(self, skip_days=1):
        try:
            logging.debug(f'set_no_water_days {self.serialID}')
            params = {'key':str(self.serialID),
                      'days':int(skip_days)}
            status, res = self._callApi('POST', '/no_water.json', params)
            if status == 'ok':
                logging.debug(f'res = {res}')
                return(res)
            else:
                return(None)
        except Exception as e:
            logging.debug(f'Exception set_no_water_days {self.serialID} {e} ')
            return(None)        
    ####################

    def get_sensor_data(self, zone_list=None ) -> dict:
        try:
            logging.debug(f'get_sensor_data {self.serialID}')
            params = {}
            if zone_list is not None:
                params['zones'] = zone_list 
            status, res = self._callApi('GET', '/sensor_data.json', params)
            if status == 'ok':
                logging.debug(f'res = {res}')
                return(res)
            else:
                return(None)
        except Exception as e:
            logging.debug(f'Exception get_evget_sensor_dataents {self.serialID} {e} ')
            return(None)

    def callNetroApi(self, method='GET',url=None, body=None):
        try:
            logging.debug(f'callNetroApi {url} {body}')
            status, res = self._callApi(method, url, body)
            response = res
            if status == 'ok':
                if 'errors' in res and len(res['errors']>0):
                    status = 'error'
                    response = res['errors']
                self.netro['meta']=res['meta']
            return(status, response)
        except KeyError as e:
            return ('error', e)

    def _callApi(self, method='GET', url=None, body=None):
        # When calling an API, get the access token (it will be refreshed if necessary)
        #self.apiLock.acquire()

        response = None
        payload = {}
        completeUrl = self.yourApiEndpoint + url

        headers = {}
        if method in [ 'PATCH', 'POST']:
            headers = {
                'Content-Type'  : 'application/json',
                'Accept'        : 'application/json',
            }
        if body is None:
            payload['key'] = self.serialID
        else:
            #payload = json.dumps(body)
            payload = body
            payload['key'] = self.serialID

        logging.debug(f' call info url={completeUrl}, header {headers}, params ={payload}')

        try:
            if method == 'GET':
                response = requests.get(completeUrl, headers=headers, params=payload)
            elif method == 'DELETE':
                response = requests.delete(completeUrl, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(completeUrl, headers=headers, json=payload)
            elif method == 'POST':
                response = requests.post(completeUrl, headers=headers, json=payload)
            elif method == 'PUT':
                response = requests.put(completeUrl, headers=headers)
            logging.debug(f'request response: {response}')

            
            
            response.raise_for_status()
            if response.status_code == 200:
                try:
                    return 'ok', response.json()
                except requests.exceptions.JSONDecodeError:
                    return 'error', response.text
            elif response.status_code == 400:
                return 'error', response.text
            elif response.status_code == 408:
                return 'offline', response.text
            elif response.status_code == 429:
                return 'overload', response.text
            else:
                return 'unknown', response.text

        except requests.exceptions.HTTPError as error:
            logging.error(f"Call { method } { completeUrl } failed: { error }")
            #self.apiLock.release()
            if response.status_code == 400:
                return('error', response.text)
            else:
                return ('unknown', response.text)