#!/usr/bin/env python3
import requests
import time
import json
from threading import Lock
from datetime import timedelta, datetime, timezone

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

#STATUS_CODE = {'STANDBY':0, 'SETUP':1, 'ONLINE':2, 'WATERING':3, 'OFFLINE':4, 'SLEEPING':5, 'POWEROFF':6,'ERROR':99,'UNKNOWN':99}
#ZONE_CONFIG = {'SMART':0, 'ASSISTANT':1,'TIMER':2,'ERROR':99,'UNKNOWN':99}
class netroAccess(object):
    def __init__(self,  serial_nbr, event_days, moist_days, sch_days):
        #super().__init__(polyglot)
        logging.info(f'Netro API initializing')
        #self.poly = polyglot
        self.serialID = serial_nbr
        self.EVENT_DAYS = event_days
        self.MOIST_DAYS = moist_days
        self.SCH_DAYS = sch_days
        self.yourApiEndpoint = 'https://api.netrohome.com/npa/v1'
        self.netro= {}
        self.update_info() #Get latest API data
        if self.netro['type'] == 'controller':
            self.update_events( self.EVENT_DAYS)
            self.update_moisture_info(self.MOIST_DAYS )
            self.update_schedules(self.SCH_DAYS)
        elif self.netro['type'] == 'sensor':
            self.update_sensor_data()

    def device_type(self) -> str:
        return(self.netro['type'])

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
    

    def status(self):
        logging.debug('status : {}'.format(self.netro['info']))
        try:
            if 'status' in self.netro['info']:
                return(self.netro['info']['status'])
            else:
                return(None)
        except KeyError as e:
            logging.error(f'ERROR - no key found {e}')
            return(None)
    
    
    def zone_list(self):
        logging.debug('zone_list')
        return(self.netro['active_zones'])

    def zone_info(self, zone_nbr=None):
        try:
            logging.debug('update_zone_info')

            if self.netro['type'] == 'controller':
                return(self.netro['active_zones'][zone_nbr])
                                            
        except KeyError as e:
            logging.error(f'Error: update_zone_info - zone may not be enabled {e}')
            return(None)
        
    def zone_status(self, zone_nbr):
        try:
            logging.debug(f'zone_status {zone_nbr} {self.netro}')
            if 'status' in self.netro['active_zones'][zone_nbr]:
                return(self.netro['active_zones'][zone_nbr]['status'])
            else:
                return('NO SCHEDULE')

        except KeyError as e:
            logging.error(f'ERROR - zone_config {e} ')
 
    def zone_config(self, zone_nbr) -> str:
        try:
            logging.debug(f'zone_config {zone_nbr}')
            return(self.netro['active_zones'][zone_nbr]['smart'])

        except KeyError as e:
            logging.error(f'ERROR - zone_config {e} ')

    def device_name(self):
        try:
            logging.debug('device_name')
            if self.netro['type'] == 'controller':
                return(self.netro['info']['device']['name'])
            elif self.netro['type'] == 'sensor':
               return(self.netro['name'])
            
            else:
                return('Unknown')
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
    
    def api_calls_remaining(self) -> int:
        return(self.netro['calls_remaining'])
    
    def update_controller_data(self):
        logging.debug('update_controller')
        self.update_info()
        self.update_moisture_info(self.MOIST_DAYS)
        self.update_events(self.EVENT_DAYS)
        self.update_schedules(self.SCH_DAYS)


    def update_info(self) -> str:
        try:
            logging.debug(f'get info ')
            status, res = self.callNetroApi('GET', '/info.json')

            if status == 'ok':
                self.extractAPIinfo(res)
                logging.debug('res = {}'.format(json.dumps(res['data'], indent=4)))                
                if 'device' in res['data']: # controller
                    self.netro['type'] = 'controller'
                    self.netro['name'] = res['data']['device']['name']
                    self.netro['info'] = res['data'] 
                    self.netro['active_zones'] = {}
                    for indx, zone in enumerate( self.netro['info']['device']['zones']):
                        if zone['enabled']:
                            self.netro['active_zones'][zone['ith']] = zone
                            self.netro['active_zones'][zone['ith']]['status'] = 'NO SCHEDULE' # defauls active zones 
                elif 'sensor_data' in res['data']: #sensor
                    self.netro['type'] ='sensor'
                    self.netro['name'] = res['data']['sensor']['name']
                    self.netro['info'] = res['data']
                logging.debug(f'self.netro {self.netro}')
                return(status)
            else:
                return(None)
        except Exception as e:
            logging.debug(f'Exception update_info {e} ')
            return(None)
        

    def _process_moisture_info(self, data):
        try:
            logging.debug(f'_process_moisture_info {json.dumps(data, indent=4)}')
            now_obj = datetime.now()
            if len(data)>0:
                for indx, m_data in enumerate(data):
                    mois_date_obj = datetime.strptime(m_data['date'], '%Y-%m-%d')
                    days_ago = (now_obj - mois_date_obj).days
                    logging.debug(f'Moisture days {days_ago}')
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
            logging.debug(f'update_moisture')

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
            logging.debug(f'Exception update_moisture {self.serialID} {e} ')
            return(None)

    def moisture(self, zone_nbr) -> int:
        logging.debug(f'moisture {zone_nbr}')
        try:
            return(self.netro['active_zones'][zone_nbr]['moisture'][1])
        except KeyError as e:
            logging.error(f'ERROR - moisture {e}')
            return (None)


    def moisture_slope(self, zone_nbr) -> int:
        logging.debug(f'moisture_slope {zone_nbr}')
        try:
            return(round(float(self.netro['active_zones'][zone_nbr]['polyfit'][0]),1))
        except KeyError as e:
            logging.error(f'ERROR - moisture_slope {e}')
            return(None)

    def _process_schedule_info(self, data):
        try:
            logging.debug(f'_process_schedule_info {json.dumps(data, indent=4)}')   
            for indx, sch_data in enumerate(data):
                sch_start_time = self.daytimestr2epocTime(sch_data['start_time'])
                sch_end_time = self.daytimestr2epocTime(sch_data['end_time'])

                zone = sch_data['zone']
                sch_type = sch_data['source']
                sch_status = sch_data['status']
                if 'next_start' not in self.netro['active_zones'][zone] and sch_status in ['VALID']:
                    self.netro['active_zones'][zone]['next_start'] = sch_start_time
                    self.netro['active_zones'][zone]['next_end'] = sch_end_time
                    self.netro['active_zones'][zone]['type'] = sch_type
                    self.netro['active_zones'][zone]['status'] = sch_status                    
                elif sch_start_time < self.netro['active_zones'][zone]['next_start'] and sch_status in ['VALID']:
                    self.netro['active_zones'][zone]['next_start'] = sch_start_time
                    self.netro['active_zones'][zone]['next_end'] = sch_end_time
                    self.netro['active_zones'][zone]['type'] = sch_type
                    self.netro['active_zones'][zone]['status'] = sch_status  
                    logging.debug('Next schedule update: {}'.format(self.netro['active_zones'][zone]))
            logging.debug(f'after process schedules {self.netro}')
        except KeyError as e:
            logging.error(f'ERROR parsing schedule data {e}')


    def next_sch_start(self, zone_nbr) -> int:
        logging.debug(f'next_sch_start {zone_nbr}')
        try:
            return(self.netro['active_zones'][zone_nbr]['next_start'])
        except KeyError:
            return(None)

    def next_sch_end(self, zone_nbr) -> int:
        logging.debug(f'next_sch_end {zone_nbr}')
        try:
            return(self.netro['active_zones'][zone_nbr]['next_end'])
        except KeyError:
            return(None)


    def update_schedules(self, next_days=None, zone_list=None ) -> dict:
        try:
            logging.debug(f'update_schedules ')
            params={}
            if isinstance(next_days, int):
                first_day, last_day = self.start_stop_dates(next_days)
                params['start_date']=first_day
                params['end_date']=last_day
            if isinstance(zone_list, list):
                params['zones'] = zone_list 
            status, res = self.callNetroApi('GET', '/schedules.json', params)
            if status == 'ok':
                self.extractAPIinfo(res)
                self._process_schedule_info(res['data']['schedules'])

            return(status)

        except Exception as e:
            logging.debug(f'Exception update_schedules {e} ')
            return(None)
        
    def _process_event_data(self, data):
        try:            
            #logging.debug(f'_process_event_data {json.dumps(data, indent=4)}')   
            for indx, e_data in enumerate(data):
                zone_nbr = None
                time = self.daytimestr2epocTime(e_data['time'])
                if e_data['event'] == 1:
                    if 'offline_event' not in self.netro:
                        self.netro['offline_event'] = time
                    elif time > self.netro['offline_event']:
                        self.netro['offline_event'] = time
                elif e_data['event'] == 2:
                    if 'online_event' not in self.netro:
                        self.netro['oline_event'] = time
                    elif time > self.netro['online_event']:
                        self.netro['online_event'] = time
                elif e_data['event'] == 3:
                    match = re.search(r'zone (\d+)', e_data['message'] )
                    if match:
                        zone_nbr = int(match.group(1))
                    #logging.debug('event 3 {} {}'.format(zone_nbr, json.dumps(self.netro['active_zones'], indent=4)))
                    if isinstance(zone_nbr, int):
                        if 'last_start' not in self.netro['active_zones'][zone_nbr]:
                            self.netro['active_zones'][zone_nbr]['last_start' ] = time
                        elif time > self.netro['active_zones'][zone_nbr]['last_start']:
                            self.netro['active_zones'][zone_nbr]['last_start' ] = time
                elif e_data['event'] == 4:
                    match = re.search(r'zone (\d+)', e_data['message'] )
                    if match:
                        zone_nbr = int(match.group(1))
                    #logging.debug(f'event 4 {zone_nbr}')
                    if isinstance(zone_nbr, int):
                        if 'last_end' not in self.netro['active_zones'][zone_nbr]:
                            self.netro['active_zones'][zone_nbr]['last_end' ] = time
                        elif time > self.netro['active_zones'][zone_nbr]['last_end' ]:
                            self.netro['active_zones'][zone_nbr]['last_end' ] = time
                else:
                    logging.error(f'ERROR - unsupported event {e_data} ')
            #logging.debug(f'after parsing event data {self.netro}')
        except KeyError as e:
            logging.error(f'ERROR parsing event data {e}')

        
    def update_events(self, days_back = None) -> dict:
        try:
            logging.debug(f'update_events {self.serialID}')
            params={}
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
            logging.debug(f'Exception update_events {self.serialID} {e} ')
            return(None)
        
    def last_sch_start(self, zone_nbr) -> int:
        logging.debug(f'last_sch_start {zone_nbr}')
        try:
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
            logging.debug(f'Exception set_status {self.serialID} {e} ')
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
            logging.debug(f'Exception set_status {self.serialID} {e} ')
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
            logging.debug(f'Exception stop_watering {self.serialID} {e} ')
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
            logging.debug(f'Exception set_skip_water_days {self.serialID} {e} ')
            return(None)        
    ####################

    def update_sensor_data(self, zone_list=None ) -> dict:
        try:
            logging.debug(f'update_sensor_data {self.serialID}')
            params = {}
            if zone_list is not None:
                params['zones'] = zone_list 
            status, res = self.callNetroApi('GET', '/sensor_data.json', params)
            if status == 'ok':
                logging.debug(f'res = {res}')
                self.extractAPIinfo(res)
                return(res)
            else:
                return(None)
        except Exception as e:
            logging.debug(f'Exception update_sensor_data {self.serialID} {e} ')
            return(None)

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