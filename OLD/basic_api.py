#!/usr/bin/env python3
import requests
import json
import re
try:
    #import udi_interface
    from udi_interface import LOGGER
    logging = LOGGER
#    ISY = udi_interface.ISY
except ImportError:
    import logging
    logging.basicConfig(level=30)


class basic_api(object):
    def __init__(self,  serial_nbr):
        self.serial_nbr = serial_nbr
        self.yourApiEndpoint = 'https://api.netrohome.com/npa/v1'
        logging.debug(f'Basic API init for serial number {self.serial_nbr}, {self.yourApiEndpoint}')

    def netroType(self):
        #self.yourApiEndpoint = 'https://api.netrohome.com/npa/v1'
        try:
            if isinstance(self.serial_nbr, str): 
        
                status, res = self.callNetroApi('GET', '/info.json')
                logging.debug(f'netroType response:{status} {res}')
                if status == 'ok':
                    if 'errors' in res and len(res['errors']>0):
                        status = 'error'
                        return(status, res['errors'])
                    elif 'device' in res['data']:
                        return ('controller',  res['data']['device']['name'])
                    elif 'sensor_data' in res['data']:
                        return('sensor',  res['data']['sensor']['name'])
                    else:
                        return('unknown', 'unknown')
            else:
                logging.error(f'netroType - serial number {self.serial_nbr} is not a string but {type(self.serial_nbr)}')
                return('unknown', 'unknown')
        except KeyError as e:
            logging.error(f'Exception - keyerror : {e}')
            return('unknown', 'unknown')
        
    def callNetroApi(self, method='GET',url=None, body=None):
        try:
            logging.debug(f'callNetroApi {url} {body}')
            payload = {}
            if body is None:
                payload['key'] = self.serial_nbr
            else:
                payload = body
                payload['key'] = self.serial_nbr
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
    

   