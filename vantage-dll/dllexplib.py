"""
    DLL export library
    
    This module implements support functions to be
    used when implementing a custom DLL export 
    python module for the Vantage Manager
    
    (c) Xena Networks 2019

"""

DLLEXP_LIB_VERSION = '1.0'

import json
from functools import partial
import http.server
import requests


class RESTRequestHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, cbserv, *args, **kwargs):
        self.cbserv = cbserv
        return super().__init__(*args, **kwargs)

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(('DLLEXP Rest server vs %s. Use POST to send data\n'%DLLEXP_LIB_VERSION).encode())
       

    def do_POST(self):
        pl = self.get_payload()
        
        resp = {'result':self.cbserv.process_post(pl)}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(resp).encode())
        

    def get_payload(self):
        payload_len = int(self.headers.get('content-length', 0))
        if payload_len==0: return {}
        payload = self.rfile.read(payload_len)
        payload = json.loads(payload.decode())
        return payload




class CallBackServer ():
    
    """
       methods which must be overridden in subclass
    """      
    def Teststarted(self,testid,param):
        return (True,'') 
    
    def TestDUTAvailable(self,testid,dutsno,param):
        return (True,'') 
    
    def TestCompleted(self,testid,dutsno,tresult,tmessage,param):
        return (True,'') 
    

    def StartServer(self,cbportno):
        
        # start the REST server for callbacks
        handler = partial(RESTRequestHandler, self)
        server = http.server.HTTPServer(('', cbportno), handler)
        print(' ready to process callbacks (Ctrl-C to stop) ...')
        try:
            server.serve_forever(0.2)
        except KeyboardInterrupt:
            pass
        print('Keyboard interrupt received - stopping HTTP / REST server')
        server.server_close()
        
        return 0
    
        
    def process_post(self,param):
        print(' processing callback event "%s" for test with id "%s"'%(param.get('event'), param.get('testid')))
        pms = param.get('params',{})
        if param.get('event')=='started':
            res,mes = self.Teststarted(testid=param.get('testid'), param=pms)
            if not res: return {'error':1,'errmes':mes}
            
        elif param.get('event')=='learned':
            res,mes = self.TestDUTAvailable(testid=param.get('testid'), dutsno=pms.get('dut'), param=pms)
            if not res: return {'error':1,'errmes':mes}
            
        elif param.get('event')=='completed':
            res,mes = self.TestCompleted(testid=param.get('testid'), dutsno=pms.get('dut'), tresult=pms.get('result'), tmessage=pms.get('resultmessage'), param=pms)
            if not res: return {'error':1,'errmes':mes}
        
        
        return {'error':0,'errmes':mes}    



"""
 wrapper class for needed Vantage API calls
"""
class VanApiWrapper:
    
    def __init__(self, chassis, auth, callbackurl=''):
        self.chassis = chassis
        self.auth = auth
        self.callbackurl = callbackurl
        self.eventsubid = ''

        
    def CreateNewSubscription(self,esfilter={},esconfig={}):
        if not esfilter: esfilter = {'user':'','cfgname':'','events':['learned','completed']}
        if not esconfig: esconfig = {'esqueue':0,'callbackurl':self.callbackurl}
        
        resp = requests.put('http://%s/vanapi/v1/evsubs/'%self.chassis, json={'esfilter':esfilter,'esconfig':esconfig}, headers={}, auth=self.auth)
        if resp.status_code!=200:
            print('Error during REST event subscription setup, HTTP response code=%s'%(resp.status_code))
            return 1
        else:
            rdat = resp.json()
            if not 'results' in rdat:
                print('Error during REST event subscription setup, incorrect JSON response=%d'%(rdat))
                return 1
            
            self.eventsubid = next(iter(rdat['results']))
            print(' %s'%(rdat['results'][self.eventsubid].get('message','')))
            
            return int(rdat['results'][self.eventsubid].get('error',0))
 
    
    def DeletOldSubscriptions(self):
        resp = requests.get('http://%s/vanapi/v1/evsubs/'%self.chassis, headers={}, auth=self.auth)
        if resp.status_code!=200:
            print('Error during REST event subscription setup, HTTP response code=%s'%(resp.status_code))
            return 1
        rdat = resp.json()
        for sub in rdat:
            if sub.get('esconfig',{}).get('callbackurl','')==self.callbackurl:
                subid = sub.get('subscrid','')
                print(' deleting existing subscription with id "%s"'%subid)
                if len(subid)>0:
                    requests.delete('http://%s/vanapi/v1/evsubs/evsubid/%s'%(self.chassis,subid), headers={}, auth=self.auth)

        return 0
    
     