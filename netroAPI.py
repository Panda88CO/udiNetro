#!/usr/bin/env python3
import requests
import time
import json
from threading import Lock
from datetime import timedelta, datetime

try:
    #import udi_interface
    from udi_interface import LOGGER
    logging = LOGGER
#    ISY = udi_interface.ISY
except ImportError:
    import logging
    logging.basicConfig(level=30)

class netroAccess(object):
    #yourApiEndpoint = 'https://fleet-api.prd.na.vn.cloud.tesla.com'
    #yourApiEndpoint = 'https://api.netrohome.com/npa/v1'
    def __init__(self,  serial_nbr):
        #super().__init__(polyglot)
        logging.info(f'Netro API initializing')
        #self.poly = polyglot
        self.serialID = serial_nbr
        self.yourApiEndpoint = 'https://api.netrohome.com/npa/v1'
        self.netro_info = {}
        self.netro_info = {}
        


    def get_info(self) -> dict:
        try:
            logging.debug(f'get info {self.serialID}')
            status, res = self._callApi('GET', '/info.json')
            if status == 'ok':
                self.netro_info = res #NOT CORRECT
                
                return(res)
            else:
                return(None)
        except Exception as e:
            logging.debug(f'Exception get_info {self.serialID} {e} ')
            return(None)
        

    def get_moisture(self, zone_list=None ) -> dict:
        try:
            logging.debug(f'get info {self.serialID}')
            params = {}
            params['zones'] = zone_list 
            status, res = self._callApi('GET', '/moistures.json', params)
            if status == 'ok':
                return(res)
            else:
                return(None)
        except Exception as e:
            logging.debug(f'Exception get_info {self.serialID} {e} ')
            return(None)
        


    
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