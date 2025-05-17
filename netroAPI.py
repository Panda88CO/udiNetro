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


STATUS_CODE = {'STANDBY':0, 'SETUP':1, 'ONLINE':2, 'WATERING':3, 'OFFLINE':4, 'SLEEPING':5, 'POWEROFF':6}

class netroAccess(object):
    def __init__(self,  serial_nbr):
        #super().__init__(polyglot)
        logging.info(f'Netro API initializing')
        #self.poly = polyglot
        self.serialID = serial_nbr
        self.yourApiEndpoint = 'https://api.netrohome.com/npa/v1'
        self.netro= {}
        self.get_info() #Get latest API data 

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
    

    def get_status(self):
        logging.debug('get_status')
        try:
            return(STATUS_CODE[self.netro['info']['status']])
        except KeyError as e:
            logging.error(f'ERROR - no key found {e}')
            return(None)
    
    
    
    def zone_list(self):
        logging.debug('zone_list')
        return(self.netro['active_zones'])

    def zone_info(self, zone_nbr=None):
        try:
            logging.debug('get_zone_info')

            if self.netro['type'] == 'controller':
                return(self.netro['active_zones'][zone_nbr])
                                            
        except KeyError as e:
            logging.error(f'Error: get_zone_info - zone may not be enabled {e}')
            return(None)
        

    def device_name(self):
        try:
            logging.debug('get_device_name')
            if self.netro['type'] == 'controller':
                return(self.netro['info']['device']['name'])
            elif self.netro['type'] == 'sensor':
               return(self.netro['name'])
            
            else:
                return('Unknown')
        except KeyError as e:
            logging.error(f'Error: get_device_name {e}')
            return(None)

    def updateAPIinfo(self, res) -> int:
        try:
            date_time_str = res['meta']['last_active']
            logging.debug('updateAPIinfo {}'.format(res['meta']))
            unix_time = self.daytimestr2epocTime(date_time_str)
            self.netro['last_api_time'] = unix_time     
            self.netro['calls_remaining'] = res['meta']['token_remaining']   
            return('ok')
        except Exception as e:
            logging.error(f'ERROR updateAPIinfo: {e} ')
            return(None)

    def get_info(self) -> str:
        try:
            logging.debug(f'get info ')
            status, res = self.callNetroApi('GET', '/info.json')

            if status == 'ok':
                self.updateAPIinfo(res)
                logging.debug('res = {}'.format(res['data']))                
                if 'device' in res['data']: # controller
                    self.netro['type'] = 'controller'
                    self.netro['name'] = res['data']['device']['name']
                    self.netro['info'] = res['data'] 
                    self.netro['active_zones'] = {}
                    for indx, zone in enumerate( self.netro['info']['device']['zones']):
                        if zone['enabled']:
                            self.netro['active_zones'][zone['ith']] = zone
                elif 'sensor_data' in res['data']: #sensor
                    self.netro['type'] ='sensor'
                    self.netro['name'] = res['data']['sensor']['name']
                    self.netro['info'] = res['data']
                logging.debug(f'self.netro {self.netro}')
                return(status)
            else:
                return(None)
        except Exception as e:
            logging.debug(f'Exception get_info {e} ')
            return(None)
        

    def _process_moisture_info(self, data):
        try:
            logging.debug(f'_process_moisture_info {data}')
            now_obj = datetime.now()
            if len(data)>0:
                for indx, m_data in enumerate(data):
                    mois_date_obj = datetime.strptime(m_data['date'], '%Y-%m-%d')
                    days_ago = (now_obj - mois_date_obj).days
                    if 'moisture' not in self.netro['active_zones'][m_data['zone']]:
                        self.netro['active_zones'][m_data['zone']]['moisture'] = {}
                    self.netro['active_zones'][m_data['zone']]['moisture'][days_ago] = m_data['moisture']
                for indx, zone in enumerate (self.netro['active_zones']):
                    d_list = []
                    m_list = []
                    for day in self.netro['active_zones'][zone]['moisture']:
                        d_list.append(day)
                        m_list.append(self.netro['active_zones'][zone]['moisture'][day])
                    x=np.array(d_list)
                    y=np.array(m_list)
                    f = np.polyfit(x,y, deg=1)
                    self.netro['active_zones'][zone]['polyfit'] = f
                    logging.debug(f'moisture slope {f[0]}')
        except KeyError as e:
            logging.error(f'ERROR parcing moisture data: {e}')                    


    def get_moisture_info(self, days_back=None, zone_list=None ) -> dict:
        try:
            logging.debug(f'get_moisture')

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
                if zone_list is None: # all zones are updated
                    logging.debug('all zones')
                    self._process_moisture_info(res['data']['moistures'])

                self.updateAPIinfo(res)
            return(status)
        except Exception as e:
            logging.debug(f'Exception get_moisture {self.serialID} {e} ')
            return(None)

    def _process_schedule_info(self, data):
        try:
            logging.debug(f'_process_schedule_info {data}')   
            for indx, sch_data in enumerate(data):
                sch_start_time = self.daytimestr2epocTime(datetime.strptime(sch_data['start_time']))
                sch_stop_time = self.daytimestr2epocTime(datetime.strptime(sch_data['stop_time']))

                zone = sch_data['zone']
                sch_type = sch_data['source']
                sch_status = sch_data['status']
                if 'next_start' not in self.netro['active_zones'][zone]:
                    self.netro['active_zones'][zone]['next_start'] = sch_start_time
                    self.netro['active_zones'][zone]['next_stop'] = sch_stop_time
                    self.netro['active_zones'][zone]['type'] = sch_type
                    self.netro['active_zones'][zone]['status'] = sch_status                    
                elif sch_start_time < self.netro['active_zones'][zone]['next_start']:
                    self.netro['active_zones'][zone]['next_start'] = sch_start_time
                    self.netro['active_zones'][zone]['next_start'] = sch_start_time
                    self.netro['active_zones'][zone]['type'] = sch_type
                    self.netro['active_zones'][zone]['status'] = sch_status  

        except KeyError as e:
            logging.error(f'ERROR parsing schedule data {e}')

    def get_schedules(self, next_days=None, zone_list=None ) -> dict:
        try:
            logging.debug(f'get_schedules ')
            params={}
            if isinstance(next_days, int):
                first_day, last_day = self.start_stop_dates(next_days)
                params['start_date']=first_day
                params['end_date']=last_day
            if isinstance(zone_list, list):
                params['zones'] = zone_list 
            status, res = self.callNetroApi('GET', '/schedules.json', params)
            if status == 'ok:':
                self._process_schedule_info(res)
                self.updateAPIinfo(res)
            return(status)

        except Exception as e:
            logging.debug(f'Exception get_schedules {e} ')
            return(None)
        
    def _process_event_data(self, data):
        try:
            
            logging.debug(f'_process_event_data {data}')   
            for indx, e_data in enumerate(data):
                zone_nbr = None
                time = self.daytimestr2epocTime(datetime.strptime(e_data['time']))
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
                    match = re.search(r'zone (\d+)', e_data['event']['message'] )
                    if match:
                        zone_nbr = int(match.group(1))
                    if isinstance(zone_nbr, int:)
                        if 'last_start' not in self.netro['active_zones'][zone_nbr]:
                            self.netro['active_zones'][zone_nbr]['last_start' ] = time
                        elif time > self.netro['active_zones'][zone_nbr]['last_start' ]:
                            self.netro['active_zones'][zone_nbr]['last_start' ] = time
                elif e_data['event'] == 4:
                    match = re.search(r'zone (\d+)', e_data['event']['message'] )
                    if match:
                        zone_nbr = int(match.group(1))
                    if isinstance(zone_nbr, int:)
                        if 'last_stop' not in self.netro['active_zones'][zone_nbr]:
                            self.netro['active_zones'][zone_nbr]['last_stop' ] = time
                        elif time > self.netro['active_zones'][zone_nbr]['last_stop' ]:
                            self.netro['active_zones'][zone_nbr]['last_stop' ] = time
                else:
                    logging.error(f'ERROR - unsupported event {e_data}')

        except KeyError as e:
            logging.error(f'ERROR parsing schedule data {e}')

        
    def get_events(self, days_back = None) -> dict:
        try:
            logging.debug(f'get_events {self.serialID}')
            params={}
            if isinstance(days_back, int):
                start_str, stop_str = self.start_stop_dates(days_back)
                params['start_date']=start_str
                params['end_date']=stop_str
            status, res = self.callNetroApi('GET', '/events.json', params)
            if status == 'ok':
                logging.debug(f'res = {res}')
                self._process_event_data(res['data']['events'])
                self.updateAPIinfo(res)
                return(res)
            else:
                return(None)
        except Exception as e:
            logging.debug(f'Exception get_events {self.serialID} {e} ')
            return(None)
        
    

    def set_status(self, statusEN=None)-> str:
        try:
            #logging.debug(f'set_status {self.serialID}')
            #params = {'key':str(self.sealID)}
            if isinstance(statusEN, int):
                params = {'status':statusEN }
                status, res = self.callNetroApi('POST', '/set_status.json', params)
                if status == 'ok':
                    self.updateAPIinfo(res)
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
                        self.updateAPIinfo(res)
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
                self.updateAPIinfo(res)
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

    def get_sensor_data(self, zone_list=None ) -> dict:
        try:
            logging.debug(f'get_sensor_data {self.serialID}')
            params = {}
            if zone_list is not None:
                params['zones'] = zone_list 
            status, res = self.callNetroApi('GET', '/sensor_data.json', params)
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