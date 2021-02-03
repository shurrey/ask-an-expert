import json
from cachetools import TTLCache
import requests
import datetime
import time
import ssl
import sys
import os
import urllib.parse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Config
import Config



class RestUserController():
    target_url = ''

    def __init__(self, target_url, token):
        
        self.target_url = target_url
        self.token = token
        
        if Config.config['verify_certs'] == 'True':
            self.verify_certs = True
        else:
            self.verify_certs = False

        self.user_info = None

    def getUserInfo(self):
        return(self.user_info)

    def getUserInfoFromLearn(self):
        OAUTH_URL = 'https://' + self.target_url + '/learn/api/public/v1/users/me'

        print('[User:getUser()] token: ' + self.token)
        #"Authorization: Bearer $token"
        authStr = 'Bearer ' + self.token
        print('[User:getUser()] authStr: ' + authStr)
        

        print("[User:getUser()] GET Request URL: " + OAUTH_URL)
        print("[User:getUser()] JSON Payload: NONE REQUIRED")
        r = requests.get(OAUTH_URL, headers={'Authorization':authStr},  verify=self.verify_certs)

        print("[User:getUser()] STATUS CODE: " + str(r.status_code) )
        #print("[User:getUser()] RESPONSE:" + str(r.text))
        if r.text:
            res = json.loads(r.text)
            print(json.dumps(res,indent=4, separators=(',', ': ')))
            self.user_info = res
            return(self.user_info)
        else:
            print("NONE")