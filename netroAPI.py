#!/usr/bin/env python3
import requests
import time
import json
#from threading import Lock
from datetime import timedelta, datetime, timezone
#from basic_api import basic_api
import numpy as np
import re
try:
    #import udi_interface
    from udi_interface import LOGGER
    logging = LOGGER
#    ISY = udi_interface.ISY
except ImportError:
    import logging
    logging.basicConfig(level=30)


class basicAPI(object):
    def __init__(self, serial_nbr):
        self.session = requests.Session()
        self.yourApiEndpoint = 'https://api.netrohome.com/npa/v1'   
        self.serialID = serial_nbr


    def callNetroApi(self, method='GET',url=None, body=None):
        try:
            logging.debug(f'callNetroApi {url} {body}')
            payload = {}
            if body is None:
                payload['key'] = self.serialID
            else:
                payload = body
                payload['key'] = self.serialID
            status, res = self._callApi(method, url, payload)
            response = res
            if status == 'ok':
                if 'errors' in res and len(res['errors']>0):
                    status = 'error'
                    response = res['errors']
            return(status, response)
        except KeyError as e:
            return ('error', e)
        

    def netroType(self):
        #self.yourApiEndpoint = 'https://api.netrohome.com/npa/v1'
        try:
            if isinstance(self.serialID, str):         
                status, res = self.callNetroApi('GET', '/info.json')
                logging.debug(f'netroType response:{status} {res}')
                if status == 'ok':
                    if 'errors' in res and len(res['errors']>0):
                        status = 'error'
                        return(status, res['errors'])
                    elif 'device' in res['data']:
                        return ('controller',  res['data']['device']['name'])
                    elif 'sensor' in res['data']:
                        return('sensor',  res['data']['sensor']['name'])
                    else:
                        return('unknown', 'unknown')
                else:
                    return('error', 'Check device online or if daily Tokens used') 
            else:
                logging.error(f'netroType - serial number {self.serialID} is not a string but {type(self.serialID)}')
                return('unknown', 'unknown')
        except KeyError as e:
            logging.error(f'Exception - keyerror : {e}')
            return('unknown', 'unknown')        

    def _callApi(self, method='GET', url=None, payload=None):
        # When calling an API, get the access token (it will be refreshed if necessary)
        #self.apiLock.acquire()

        response = None
        #payload = body
        completeUrl = self.yourApiEndpoint + url

        headers = {}
        if method in [ 'PATCH', 'POST']:
            headers = {
                'Content-Type'  : 'application/json',
                'Accept'        : 'application/json',
            }
        #if payload is not None:
        #    payload = json.dumps(payload)
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
    
#STATUS_CODE = {'STANDBY':0, 'SETUP':1, 'ONLINE':2, 'WATERING':3, 'OFFLINE':4, 'SLEEPING':5, 'POWEROFF':6,'ERROR':7,'UNKNOWN':99}
#ZONE_CONFIG = {'SMART':0, 'ASSISTANT':1,'TIMER':2,'ERROR':99,'UNKNOWN':99}
class netroAccess(basicAPI):
    def __init__(self,  serial_nbr, event_days=-7, moist_days=-3, sch_days=7, dev_noly = False):
        super().__init__(serial_nbr)

        logging.info(f'Netro API initializing')
        self.serialID = serial_nbr
        self.EVENT_DAYS = event_days
        self.MOIST_DAYS = moist_days
        self.SCH_DAYS = sch_days
        self.defined_schedules = 0
        
        self.data_ready = False
        self.DEV_TYPE = None
        self.netro = {}
        self.netro['active_zones'] = {}
        self.update_info() #Get latest API data
        logging.debug(f'self.nero: {self.netro}')
        if 'device_type' in self.netro:
            if self.netro['device_type'] == 'controller':
                self.update_events( self.EVENT_DAYS)
                self.update_moisture_info(self.MOIST_DAYS )
                self.update_schedules(self.SCH_DAYS)
            elif self.netro['device_type'] == 'sensor':
                self.update_sensor_data()
            self.data_ready = True
        else:
            logging.error(f'NO DATA from sensor {self.netro}')
            self.data_ready = False



    def device_type(self) -> str:
        return(self.netro['device_type'])

    def daytimestr2epocTime(self, date_time_str) -> int:
        date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M:%S')
        date_time_obj = date_time_obj.replace(tzinfo=timezone.utc)
        unix_time = int(date_time_obj.timestamp())
        return(unix_time)



    def daystr2epocTime(self, time_str) -> int:
        date_time_obj = datetime.strptime(time_str, "%Y-%m-%d")
        date_time_obj = date_time_obj.replace(tzinfo=timezone.utc)
        unix_time = int(date_time_obj.timestamp())
        return(unix_time)

    def start_stop_dates(self, days):
        day0 = datetime.now()
        start_day = ''
        end_day='' 
        if isinstance(days, int):
            day2  = day0 + timedelta(days=days)
            if days > 0:
                start_day = day0.strftime("%Y-%m-%d")
                end_day =  day2.strftime("%Y-%m-%d")
            else:
                end_day = day0.strftime("%Y-%m-%d")
                start_day =  day2.strftime("%Y-%m-%d")              

        return(start_day, end_day)
    

    """
    def status(self):
        logging.debug('status : {}'.format(self.netro['info'][self.DEV_TYPE]))
        try:
            if 'status' in self.netro['info'][self.DEV_TYPE]:
                return(self.netro['info'][self.DEV_TYPE]['status'])
            else:
                return(None)
        except KeyError as e:
            logging.error(f'ERROR - no key found {e}')
            return(None)
    
    def total_zones(self):
        logging.debug('total_zones')
        return(self.netro['total_zones'])
    
    def zone_list(self):
        logging.debug('zone_list')
        return(self.netro['active_zones'])

    def zone_info(self, zone_nbr=None):
        try:
            logging.debug('update_zone_info')

            if self.netro['device_type'] == 'controller':
                return(self.netro['active_zones'][zone_nbr])
                                            
        except KeyError as e:
            logging.error(f'Error: update_zone_info - zone may not be enabled {e}')
            return(None)


    def zone_source(self, zone_nbr):
        try:
            logging.debug(f'zone_source {zone_nbr} {self.netro}')
            if 'status' in self.netro['active_zones'][zone_nbr]:
                return(self.netro['active_zones'][zone_nbr]['status'])
            else:
                return('NO SCHEDULE')

        except KeyError as e:
            logging.error(f'ERROR - zone_config {e} ')
 
    
    def zone_status(self, zone_nbr):
        try:
            logging.debug(f'zone_status {zone_nbr} {self.netro}')
            if 'status' in self.netro['active_zones'][zone_nbr]:
                return(self.netro['active_zones'][zone_nbr]['status'])
            else:
                return('NO SCHEDULE')

        except KeyError as e:
            logging.error(f'ERROR - zone_config {e} ')
    """
    def system_status(self):
        try:
            logging.debug('system_status')
            if 'status' in self.netro['info'][self.DEV_TYPE]:
                return(self.netro['info'][self.DEV_TYPE]['status'])
            else:
                return(None)
        except KeyError as e:
            logging.error(f'ERROR - system_status {e} ')
            return(None)

    """
    def zone_config(self, zone_nbr) -> str:
        try:
            logging.debug(f'zone_config {zone_nbr}')
            return(self.netro['active_zones'][zone_nbr]['smart'])

        except KeyError as e:
            logging.error(f'ERROR - zone_config {e} ')
    """
    def device_name(self):
        try:
            logging.debug('device_name')
            #if self.netro['device_type'] == 'controller':
            return(self.netro['info'][self.DEV_TYPE]['name'])
            #elif self.netro['device_type'] == 'sensor':
            #   return(self.netro['name'])            
            #else:
            #    return('Unknown')
        except KeyError as e:
            logging.error(f'Error: device_name {e}')
            return(None)

    def extractAPIinfo(self, res) -> int:
        try:
            date_time_str = res['meta']['last_active']
            logging.debug('extractAPIinfo {}'.format(json.dumps(res['meta'], indent=4)))
            unix_time = self.daytimestr2epocTime(date_time_str)
            self.netro['last_api_time'] = unix_time     
            self.netro['calls_remaining'] = res['meta']['token_remaining']   
            return('ok')
        except Exception as e:
            logging.error(f'ERROR extractAPIinfo: {e} ')
            return(None)

    def api_last_update(self) -> int:
        return(self.netro['last_api_time'])
    
    
    def update_controller_data(self):
        logging.debug('update_controller')
        self.update_info()
        self.update_moisture_info()
        self.update_schedules()
        self.update_events()

    """
    def last_end_time(self):
        logging.debug('last_end_time {}'.format(self.netro['last_end']))
        try:
            return(self.netro['last_end'])
        except KeyError as e:
            logging.error(f'EXCEPTION - {e}')
            return(None)
        
    def last_start_time(self):
        logging.debug('last_strart_time {}'.format(self.netro['last_start']))
        try:
            return(self.netro['last_start'])
        except KeyError as e:
            logging.error(f'EXCEPTION - {e}')
            return(None)
 
    def next_end_time(self):
        logging.debug('next_end_time {}'.format(self.netro['next_end']))
        try:
            return(self.netro['next_end'])
        except KeyError as e:
            logging.error(f'EXCEPTION - {e}')
            return(None)
        
    def next_start_time(self):
        logging.debug('next_start_time {}'.format(self.netro['next_start']))
        try:
            return(self.netro['next_start'])
        except KeyError as e:
            logging.error(f'EXCEPTION - {e}')
            return(None)

    def last_offline_event(self):
        logging.debug(f'last_offline_event {self.netro}')
        try:
            return(self.netro['offline_event'])
        except KeyError as e:
            logging.error(f'EXCEPTION - {e}')
            return(None)
        
    def last_online_event(self):
        logging.debug(f'last_online_event {self.netro}')
        try:
            return(self.netro['online_event'])
        except KeyError as e:
            logging.error(f'EXCEPTION - {e}')
            return(None)
    

    def get_battery_level(self):
        logging.debug('get_battery_level {}'.format(self.netro['info'][self.DEV_TYPE]))
        if 'battery_level' in self.netro['info'][self.DEV_TYPE]:
            return(round(self.netro['info'][self.DEV_TYPE]['battery_level']*100,1))
        else:
            return(None)

    def apicalls_remaining(self):
        logging.debug('apicalls_remaining {}'.format(self.netro))
        if 'calls_remaining' in self.netro:
            return(self.netro['calls_remaining'])
        else:
            return(None)
        
    def last_API(self):
        logging.debug('last_API {}'.format(self.netro['last_api_time']))
        if 'last_api_time' in self.netro:
            return(self.netro['last_api_time'])
        else:
            return(None)     
    """
    def get_controller_info(self, key):
        try:
            logging.debug(f'get_controller_info; {key} = {self.netro[key]}')
            return(self.netro[key])
        except KeyError as e:
            logging.error(f'Exception get_controller_info {key} : {e}  - {self.netro}')      
            return(None)

    def get_zone_info(self, zone_nbr, key):
        try:
            #logging.debug(f"get_zone_info for zone {zone_nbr} : {key}: {self.netro}")
            logging.debug(f"get_zone_info for zone {zone_nbr} : {key}: {self.netro['active_zones'][zone_nbr]}")
            logging.debug(f"get_zone_info for zone - self.netro: {self.netro}")
            return(self.netro['active_zones'][zone_nbr][key])
        except KeyError as e:
            if key in ['last_start', 'last_end', 'next_start', 'next_end'] and self.netro['active_zones'][zone_nbr]['status'] in ['NO SCHEDULE']:
                return(None)
            else:
                logging.debug(f"Exception get_zone_info {zone_nbr} {key} -{e} : {self.netro['active_zones']}")
                return(None)
    def update_info(self) -> str:
        try:
            
            status, res = self.callNetroApi('GET', '/info.json')
            logging.debug(f'update_info response:{status} {res}')

            if status == 'ok':
                self.extractAPIinfo(res)
                logging.debug('res = {}'.format(json.dumps(res['data'], indent=4)))    


                if 'device' in res['data']:
                    self.DEV_TYPE = 'device'
                    logging.debug(f"Coltroller selected {res['data'][self.DEV_TYPE ]['status']}") # controller
                    self.netro['device_type'] = 'controller'
                    
                    if 'battery_level' in res['data'][self.DEV_TYPE]:
                        self.netro['battery_level'] = res['data'][self.DEV_TYPE]['battery_level']
                    else:
                        self.netro['battery_level'] = None
                    if 'last_active' in res['data'][self.DEV_TYPE]:
                        self.netro['last_active'] = self.daytimestr2epocTime(res['data'][self.DEV_TYPE]['last_active'])
                    else:
                        self.netro['last_active'] = None
                    if 'status' in res['data'][self.DEV_TYPE]:
                        logging.debug(f"STATUS {res['data'][self.DEV_TYPE]['status']}")
                        self.netro['status'] = res['data'][self.DEV_TYPE]['status']
                    else:
                        self.netro['status'] = None
                    self.netro['name'] = res['data'][self.DEV_TYPE ]['name']
                    self.netro['info'] = res['data'] 
                    #self.netro['status'] = res['data']['status']
                    self.netro['total_zones'] = res['data'][self.DEV_TYPE]['zone_num']

                    self.netro['last_start'] = None
                    self.netro['last_end'] = None
                    self.netro['next_start'] = None
                    self.netro['next_end'] = None
                    self.netro['offline_event'] = None
                    self.netro['online_event'] = None                    

                    
                    for indx, zone in enumerate( self.netro['info'][self.DEV_TYPE]['zones']):
                        #self.netro['total_zones'] = len(self.netro['info']['device']['zones'])
                        if zone['enabled']:
                            self.netro['active_zones'][zone['ith']] = zone # includes name, smart, enabled etc
                            self.netro['active_zones'][zone['ith']]['status'] = 'NO SCHEDULE' # defauls active zones 
                    self.netro['nbr_active_zones'] = len(self.netro['active_zones'])
                elif 'sensor' in res['data']: #sensor
                    self.netro['device_type'] ='sensor'
                    self.DEV_TYPE = 'sensor'
                    if 'battery_level' in res['data'][self.DEV_TYPE]:
                        self.netro['battery_level'] = res['data'][self.DEV_TYPE]['battery_level']
                    else:
                        self.netro['battery_level'] = None
                    if 'last_active' in res['data'][self.DEV_TYPE]:
                        self.netro['last_active'] = self.daytimestr2epocTime(res['data'][self.DEV_TYPE]['last_active'])
                    else:
                        self.netro['last_active'] = None
                    if 'status' in res['data'][self.DEV_TYPE]:
                        self.netro['status'] = res['data'][self.DEV_TYPE]['status']
                    else:
                        self.netro['status'] = None
                    self.netro['name'] = res['data'][self.DEV_TYPE]['name']
                    self.netro['info'] = res['data']
                else:
                    self.netro['device_type'] = 'Unknown'
                    self.DEV_TYPE = 'unknown'
                    return('error')
                logging.debug(f'self.netro {self.netro}')

                return(status)
            else:
                return(None)
        except Exception as e:
            logging.error(f'Exception update_info {e} ')
            return(None)
        

    def _process_moisture_info(self, data):
        try:
            logging.debug(f'_process_moisture_info {json.dumps(data, indent=4)}')
            now_obj = datetime.now()
            if len(data)>0:
                for indx, m_data in enumerate(data):
                    mois_date_obj = datetime.strptime(m_data['date'], '%Y-%m-%d')
                    days_ago = (now_obj - mois_date_obj).days
                    #logging.debug(f'Moisture days {days_ago}')
                    if 'moisture' not in self.netro['active_zones'][m_data['zone']]:
                        self.netro['active_zones'][m_data['zone']]['moisture'] = {}
                    self.netro['active_zones'][m_data['zone']]['moisture'][days_ago] = m_data['moisture']
                for indx, zone in enumerate (self.netro['active_zones']):
                    d_list = []
                    m_list = []
                    for day in self.netro['active_zones'][zone]['moisture']:
                        d_list.append(-day)
                        m_list.append(self.netro['active_zones'][zone]['moisture'][day])
                    x=np.array(d_list)
                    y=np.array(m_list)
                    f = np.polyfit(x,y, deg=1)
                    self.netro['active_zones'][zone]['polyfit'] = f
                    #logging.debug(f'moisture slope {f[0]}')
            logging.debug(f' after processing moisture data {self.netro}')
        except KeyError as e:
            logging.error(f'ERROR parcing moisture data: {e}')                    




    def update_moisture_info(self, days_back=None, zone_list=None ) -> dict:
        try:
            logging.debug(f'update_moisture {days_back}')
            if days_back is None:
                days_back = self.MOIST_DAYS
            params = {}
            if isinstance(days_back, int):
                start_str, stop_str = self.start_stop_dates(days_back)
                params['start_date']=start_str
                params['end_date']=stop_str
            if isinstance(zone_list, list):
                params['zones'] = zone_list 
            status, res = self.callNetroApi('GET', '/moistures.json', params)
            if status == 'ok':
                logging.debug(f'res = {res}') 
                self.extractAPIinfo(res)         
                if zone_list is None: # all zones are updated
                    logging.debug('all zones')
                    self._process_moisture_info(res['data']['moistures'])
            return(status)
        except Exception as e:
            logging.error(f'Exception update_moisture {self.serialID} {e} ')
            return(None)

    
    def moisture(self, zone_nbr) -> int:
        logging.debug(f'moisture {zone_nbr}')
        try:
            if 'moisture' in self.netro['active_zones'][zone_nbr]:
                return(self.netro['active_zones'][zone_nbr]['moisture'][1])
            else:
                return(None)
        except KeyError as e:
            logging.error(f'ERROR - moisture {e}')
            return (None)
    
    def moisture_slope(self, zone_nbr) -> int:
        logging.debug(f'moisture_slope {zone_nbr}')
        try:
            if 'polyfit' in self.netro['active_zones'][zone_nbr]:
                return(round(float(self.netro['active_zones'][zone_nbr]['polyfit'][0]),1))
            else:
                return (None)
        except KeyError as e:
            logging.error(f'ERROR - moisture_slope {e}')
            return(None)

    def _process_schedule_info(self, data):
        try:
            logging.debug(f'_process_schedule_info data {json.dumps(data, indent=4)}')   
            logging.debug(f'_process_schedule_info self.netro {self.netro}')   
            for indx, sch_data in enumerate(data):
                sch_start_time = self.daytimestr2epocTime(sch_data['start_time'])
                sch_end_time = self.daytimestr2epocTime(sch_data['end_time'])

                zone = sch_data['zone']
                sch_source = sch_data['source']
                sch_status = sch_data['status']
                #if sch_status in ['VALID'] and sch_source == self.netro['active_zones'][zone]['smart']:
                if sch_status in ['VALID'] :   
                    if 'next_start' not in self.netro['active_zones'][zone]:
                        self.netro['active_zones'][zone]['next_start'] = sch_start_time
                        self.netro['active_zones'][zone]['next_end'] = sch_end_time
                        self.netro['active_zones'][zone]['source'] = sch_source
                        self.netro['active_zones'][zone]['status'] = sch_status
                    elif  sch_start_time < self.netro['active_zones'][zone]['next_start']:
                        self.netro['active_zones'][zone]['next_start'] = sch_start_time
                        self.netro['active_zones'][zone]['next_end'] = sch_end_time
                        self.netro['active_zones'][zone]['source'] = sch_source
                        self.netro['active_zones'][zone]['status'] = sch_status  
                    logging.debug('Next schedule update: {}'.format(self.netro['active_zones'][zone]))
                if self.netro['next_start'] is None:
                    self.netro['next_start'] = sch_start_time
                elif sch_start_time < self.netro['next_start']:
                    self.netro['next_start'] = sch_start_time 
                if self.netro['next_end'] is None:
                    self.netro['next_end'] = sch_end_time
                elif sch_end_time < self.netro['next_end']:
                    self.netro['next_end'] = sch_end_time 
            logging.debug(f'next_start {self.netro["next_start"]} next_end {self.netro["next_end"]}')

                
            logging.debug(f'after _process_schedule_info {self.netro}')
        except KeyError as e:
            logging.error(f'ERROR parsing schedule data {e}')


    def next_sch_start(self, zone_nbr) -> int:
        logging.debug(f'next_sch_start {zone_nbr}')
        try:
            if self.netro['active_zones'][zone_nbr]['status'] in ['NO SCHEDULE']:
                return('NO SCHEDULE')
            elif 'next_start' in self.netro['active_zones'][zone_nbr]:
                return(self.netro['active_zones'][zone_nbr]['next_start'])
            else:
                return('NO SCHEDULE')
        except KeyError:
            return(None)

    def next_sch_end(self, zone_nbr) -> int:
        logging.debug(f'next_sch_end {zone_nbr}')
        try:
            if self.netro['active_zones'][zone_nbr]['status'] in ['NO SCHEDULE']:
                return('NO SCHEDULE')
            elif 'next_end' in self.netro['active_zones'][zone_nbr]:            
                return(self.netro['active_zones'][zone_nbr]['next_end'])
            else:
                return('NO SCHEDULE')

        except KeyError:
            return(None)


    def update_schedules(self, next_days=None, zone_list=None ) -> dict:
        try:
            logging.debug(f'update_schedules {next_days}')
            params={}
            if next_days is None:
                next_days = self.SCH_DAYS
            if isinstance(next_days, int):
                first_day, last_day = self.start_stop_dates(next_days)
                params['start_date']=first_day
                params['end_date']=last_day
            if isinstance(zone_list, list):
                params['zones'] = zone_list 
            status, res = self.callNetroApi('GET', '/schedules.json', params)
            if status == 'ok':
                self.extractAPIinfo(res)
                if 'schedules' in res['data'] and res['data']['schedules'] is not None:
                    self._process_schedule_info(res['data']['schedules'])
                    self.defined_schedules =  len(res['data']['schedules'])
                else:
                    self.defined_schedules = 0
                    

            return(status)

        except Exception as e:
            logging.error(f'Exception update_schedules {e} ')
            return(None)
   

    def _process_event_data(self, data):
        try:            
            logging.debug(f'_process_event_data {json.dumps(data, indent=4)}')   
            for indx, e_data in enumerate(data):
                zone_nbr = None
                time = self.daytimestr2epocTime(e_data['time'])
                if e_data['event'] == 1:
                    if self.netro['offline_event'] is None:
                        self.netro['offline_event'] = time
                    elif time > self.netro['offline_event']:
                        self.netro['offline_event'] = time
                elif e_data['event'] == 2:
                    if self.netro['online_event'] is None:
                        self.netro['online_event'] = time
                    elif time > self.netro['online_event']:
                        self.netro['online_event'] = time
                elif e_data['event'] == 3:
                    match = re.search(r'zone (\d+)', e_data['message'] )
                    if match:
                        zone_nbr = int(match.group(1))
                    logging.debug('event 3 {} {}'.format(zone_nbr, json.dumps(self.netro['active_zones'], indent=4)))
                    if isinstance(zone_nbr, int):
                        if 'last_start' not in self.netro['active_zones'][zone_nbr]:
                            self.netro['active_zones'][zone_nbr]['last_start' ] = time
                        elif time > self.netro['active_zones'][zone_nbr]['last_start']:
                            self.netro['active_zones'][zone_nbr]['last_start' ] = time
                        if self.netro['last_start'] is None:
                            self.netro['last_start'] = self.netro['active_zones'][zone_nbr]['last_start' ] 
                        elif self.netro['last_start'] < self.netro['active_zones'][zone_nbr]['last_start' ]:
                            self.netro['last_start'] = self.netro['active_zones'][zone_nbr]['last_start' ] 
                elif e_data['event'] == 4:
                    match = re.search(r'zone (\d+)', e_data['message'] )
                    if match:
                        zone_nbr = int(match.group(1))
                    logging.debug(f'event 4 {zone_nbr} {json.dumps(self.netro["active_zones"], indent=4)}')
                    if isinstance(zone_nbr, int):
                        if 'last_end' not in self.netro['active_zones'][zone_nbr]:
                            self.netro['active_zones'][zone_nbr]['last_end' ] = time
                        elif time > self.netro['active_zones'][zone_nbr]['last_end' ]:
                            self.netro['active_zones'][zone_nbr]['last_end' ] = time
                        if self.netro['last_end'] is None:
                            self.netro['last_end'] = self.netro['active_zones'][zone_nbr]['last_end' ] 
                        elif self.netro['last_end'] < self.netro['active_zones'][zone_nbr]['last_end']:
                            self.netro['last_end'] = self.netro['active_zones'][zone_nbr]['last_end' ]                             
                else:
                    logging.error(f'ERROR - unsupported event {e_data} ')
            logging.debug(f'after parsing event data {self.netro}')
        except KeyError as e:
            logging.error(f'ERROR parsing event data {e}')

        
    def update_events(self, days_back = None) -> dict:
        try:
            logging.debug(f'update_events {self.serialID} {days_back}')
            params={}
            if days_back is None:
                days_back = self.EVENT_DAYS 
            if isinstance(days_back, int):
                start_str, stop_str = self.start_stop_dates(days_back)
                params['start_date']=start_str
                params['end_date']=stop_str
            status, res = self.callNetroApi('GET', '/events.json', params)
            if status == 'ok':
                logging.debug(f'res = {res}')
                self.extractAPIinfo(res)
                self._process_event_data(res['data']['events'])

                return(res)
            else:
                return(None)
        except Exception as e:
            logging.error(f'Exception update_events {self.serialID} {e} ')
            return(None)
        
    def last_sch_start(self, zone_nbr) -> int:
        logging.debug(f'last_sch_start {zone_nbr}')
        try:
            if self.netro['active_zones'][zone_nbr]['status'] in ['NO SCHEDULE']:
                return('NO SCHEDULE')
            else:
                return(self.netro['active_zones'][zone_nbr]['last_start'])
        except KeyError:
            return(None)
        

    def last_sch_end(self, zone_nbr) -> int:
        logging.debug(f'last_sch_end {zone_nbr}')
        try:
            return(self.netro['active_zones'][zone_nbr]['last_end'])
        except KeyError:
            return(None)

    def set_status(self, statusEN=None)-> str:
        try:
            #logging.debug(f'set_status {self.serialID}')
            #params = {'key':str(self.sealID)}
            if isinstance(statusEN, int):
                params = {'status':statusEN }
                status, res = self.callNetroApi('POST', '/set_status.json', params)
                if status == 'ok':
                    self.extractAPIinfo(res)
                    logging.debug(f'res = {res}')
                    self.netro['status'] = statusEN
    
                    return(status)
                else:
                    return(None)
            return(None)
        except Exception as e:
            logging.error(f'Exception set_status {self.serialID} {e} ')
            return(None)
        
    def set_watering(self, duration=1, delay=0, zone = None) -> str:
        try:
            logging.debug(f'set_watering  {duration} {delay} {zone}')
            
            if isinstance(duration, int):
                params = {'duration':duration}
                if isinstance(delay, int):
                    params['delay']=delay
                if isinstance(zone, int):
                    params['zones'] = [zone]
                    status, res = self.callNetroApi('POST', '/water.json', params)

                    if status == 'ok':
                        self.extractAPIinfo(res)
                        logging.debug(f'res = {res}')
                        return(status)
                else:
                    return(None)
            else:
                return(None)
        except Exception as e:
            logging.error(f'Exception set_status {self.serialID} {e} ')
            return(None)

    def stop_watering(self)  -> str:
        try:
            logging.debug(f'stop_watering ')
            status, res = self.callNetroApi('POST', '/stop_water.json')
            if status == 'ok':
                self.extractAPIinfo(res)
                logging.debug(f'res = {res}')
                return(status)
            else:
                return(None)
        except Exception as e:
            logging.error(f'Exception stop_watering {self.serialID} {e} ')
            return(None)
        
    def set_skip_water_days(self, skip_days=None) -> str:
        try:
            logging.debug(f'set_skip_water_days {skip_days}')
            if isinstance(skip_days, int):
                params = {'days':skip_days}
                status, res = self.callNetroApi('POST', '/no_water.json', params)
                if status == 'ok':
                    logging.debug(f'res = {res}')
                    return(status)
            else:
                return(None)
        except Exception as e:
            logging.error(f'Exception set_skip_water_days {self.serialID} {e} ')
            return(None)        
    ####################

    def update_sensor_data(self) -> dict:
        try:
            logging.debug(f'update_sensor_data {self.serialID} {self.netro}')
            params = {}
            res = {}
            #status = self.update_info()

            if self.netro['status'] in ['ONLINE']:
                start_str, stop_str = self.start_stop_dates(-1)
                params['start_date']=start_str
                params['end_date']=stop_str
                status, tmp_res = self.callNetroApi('GET', '/sensor_data.json', params)
                logging.debug(f'status {status}  tmp_res{tmp_res}')
                self.extractAPIinfo(tmp_res)                
                if status == 'ok':
                    logging.debug('status {} '.format(tmp_res['data']['sensor_data']))
                    if len(tmp_res['data']['sensor_data']) > 0:
                        res = tmp_res['data']['sensor_data'][0]
                        logging.debug('res {} '.format(res))
                        for key in res:
                            if key not in self.netro:
                                self.netro[key] = res[key]
                        res['time'] = self.daytimestr2epocTime(res['time'])
                        #self.netro['sensor_data'] = res
                        #self.netro['sensor_data']['time'] = self.daytimestr2epocTime(res['time'])
                        logging.debug(f'res = {json.dumps(res, indent=4)}')
                        
                
                return(res)
            else:
                return(None)
        except Exception as e:
            logging.error(f'Exception update_sensor_data {self.serialID} {e} ')
            return(None)

    def get_sensor_data(self, key):
        try:

            logging.debug(f'get Sensor Data for {key} = {self.netro[key]}')
            return(self.netro[key])
        except KeyError as e:
            logging.error(f'Exception get_sensor_data {key} not in data {self.netro} ')
            return(None)

    

    
    
    