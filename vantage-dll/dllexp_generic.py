"""
    DLL export program
    
    This file is a template main program 
    which can be used to implement custom results export
    via customer supplied DLLs and by using the 
    Vantage Manager REST API.
    
    (c) Xena Networks 2019
    
    Environment required:
       python vs 3.4.3  (other versions may work too)
       
       python install files can be found at https://www.python.org/downloads/windows/
       
       in addition to the std. python setup a single 
       package must be installed, use this command:
       pip install requests
       
       IMPORTANT!
       Python is available in 32 and 64 bit versions. The program will run with either, 
       but if the DLL is a 32 bit DLL then a 32bit version of python must be used - and vice verca.

       
    Execution:       
    
       python dllexp_generic.py [options]
       
       Use -h option to see all available options
    
       Note if this programs is run on PC with a non chinese codepage, the following 
       two commands must be executed at the CMD prompt before the program is run:
        chcp 936
        set PYTHONIOENCODING=936
       This will ensure chinese is displayed correctly on the console.
       
       
    
    Enjoy ...

"""


import sys
import getopt
import os
import re
import socket
import json
import time
import requests
from operator import __mod__

PROGRAM_VERSION = '1.5'


"""
 The following settings are defaults for testing.
 The real settings should be supplied on the command line
 run "python dllexp_generic -h" to list options  
"""
# information about Vantage Manager chassis
CHASSIS_ADDRESS = '192.168.1.137'
CHASSIS_USERNAME = 'demoa'
CHASSIS_PASSWORD = 'Xena2018'

# information about the address where this script runs
DEFAULT_CBACK_PORT = 8082
DEFAULT_CBACK_ADR = '192.168.1.59'


"""
  settings useful for integration and module testing
  
"""
DLL_ONLINE = True  # set to false when testing without DB connection, no DLL calls will be made
CHASSIS_ONLINE = True # set to false when testing without chassis
DLL_ALWAYS_SUCCESS = False # set to true to force success of all DLL calls


"""
  test config data 
"""  
# test values, must be replace by real values from command line



from dllexplib import CallBackServer, VanApiWrapper, DLLEXP_LIB_VERSION

"""
 replace test_dll with import from custom DLL wrapper here
 
"""  
from test_dll import TestDll


"""
 this is the main class of this program
 it is derived from the CallBackServer which contains 
 the parts that are common to all implementations
 
 the main class may need to be modifed to support functionality and 
 interface of various DLL types
 
"""
class dllexpMain(CallBackServer):
    
    def __init__(self, *args, **kwargs):
        self.cbportno = DEFAULT_CBACK_PORT
        self.cbadr = DEFAULT_CBACK_ADR
        self.chassis = CHASSIS_ADDRESS
        self.li_user = CHASSIS_USERNAME
        self.li_passw = CHASSIS_PASSWORD
        
        self.dll = None
        
    """
      this method is called when a callback is received when a new DUT 
      has been attached and the serial no obtained 
    """
    def TestDUTAvailable(self,testid,dutsno,param={}):
       
        if DLL_ONLINE:
            err, errmes = self.dll.CheckSerial(user=param.get('testerid'),serial=dutsno)
            if (DLL_ALWAYS_SUCCESS) or (err==0):
                print(' validation of serial number %s was successful, continue testing'%dutsno)
                return (True,'External DB validation of serial number "%s" was successful, continue testing'%dutsno)
            else:
                print(' validation of serial number %s failed, aborting test'%dutsno)
                return (False, 'External DB validation of serial number "%s" failed, test aborted. Cause:%s '%(dutsno,errmes))
                
        else:
            print(' DLL OFFLINE - skipping call')
            return (True,'External DB validation: DLL calls skipped')    

    
    """
      this method is called when a test completed and a callback is received 
      it is used to store the test result in an external DB
    """
    def TestCompleted(self,testid,dutsno,tresult,tmessage,param={}):
        if DLL_ONLINE:
            err, errmes = self.dll.WriteTestData(user=param.get('testerid'),serial=dutsno,result=tresult,testlog=tmessage)
            if (DLL_ALWAYS_SUCCESS) or (err==0):
                print(' storage of test result "%s" for serial number %s was successful'%(tresult,dutsno))
                return (True,'External DB storage of test result for serial number %s was successful'%dutsno)
            else:
                print(' storage of test result "%s" for serial number %s failed'%(tresult,dutsno))
                return (False, 'External DB storage of test result for serial number %s failed: %s'%(dutsno,errmes))
                
        else:
            print(' DLL OFFLINE - skipping call')
            return (True,'External DB storage: DLL calls skipped')    
        
    
    
    
    
    def SetupSubscription(self):
        """
          check if there is already subsription(s) to my url
          and if so delete them  
        """
        res = self.vanapi.DeletOldSubscriptions()
        if res!=0: return res
        
        
        """
          filter detemines what events are subscribed to:
          set user to chassis username or empty to get events for all users
          set cfgname to get events from specific test configuration - or empty to get from all
          set events to get events when DUT MAC has been learned and when test completes
        """
        esfilter = {'user':'','cfgname':'','events':['learned','completed']}
        esconfig = {'esqueue':0,'callbackurl':self.callbackurl}
       
        res = self.vanapi.CreateNewSubscription(esfilter,esconfig)
        if res!=0: return res
        
        return 0
    
        
    def print_help_exit(self):
        
        print (' DLLEXP HTTP / REST server (C) Xena Networks 2019')
        print ('Usage: python3 %s [options]'%sys.argv[0])
        print ('  options :')
        print ('    -h          # print help text')
        print ('    -p <port>   # specify alternate port number (default=8082)')
        print ('    -a <ip>     # specify network address (default=192.168.1.100)')
        print ('    -c <ip>     # specify chassis network address (default=192.168.1.227)')
        print ('    -u <username>  # specify username for Vantage chassis login (default=demoa)')
        print ('    -w <password>  # specify password for Vantage chassis login')
        return 1
 
    
    def main(self):
         
        try:
            opts, args = getopt.getopt(sys.argv[1:],'hd:n:o:w:u:p:a:c:',[])
        except getopt.GetoptError:
            return self.print_help_exit()+1
        
        for opt, arg in opts:
            if opt == '-h':
                return self.print_help_exit()
            elif opt == '-p':
                self.cbportno = int(arg)
            elif opt == '-a':
                self.cbadr = str(arg)
            elif opt == '-c':
                self.chassis = str(arg)
            elif opt == '-u':
                self.li_user = str(arg)
            elif opt == '-w':
                self.li_passw = str(arg)
                

        print('DLLEXP HTTP / REST server vs %s, library vs %s' % (PROGRAM_VERSION,DLLEXP_LIB_VERSION))
        
        self.callbackurl = 'http://%s:%s'%(self.cbadr,self.cbportno)


        # load the DLL
        print(' loading DLL interface')
        self.dll = TestDll()
        self.dll.loaddll()
        
        if not CHASSIS_ONLINE:
            # used for module testing
            print ('err=%s, message=%s'% self.TestDUTAvailable(testid='AAAABBB',dutsno='5078B3A3707A',param={'testerid':'wong'}))
            print ('------')
            print ('err=%s, message=%s'% self.TestCompleted(testid='AAAABBB',dutsno='5078B3A3707A',param={'testerid':'wong'},tresult='PASSED',tmessage='Test log message : Test ok'))
            print ('------')
            print ('err=%s, message=%s'% self.TestDUTAvailable(testid='XXXXZZB',dutsno='',param={'testerid':'peter'}))
            print ('------')
            print ('err=%s, message=%s'% self.TestCompleted(testid='XXXXZZB',dutsno='',param={'testerid':'peter'},tresult='FAILED',tmessage='Test log message : Test failed'))
            print ('------')
            sys.exit(0)
        
        # intitialize Vantage API
        self.vanapi = VanApiWrapper(chassis=self.chassis,auth=(self.li_user, self.li_passw),callbackurl=self.callbackurl)
        
        
        # setup the event subsription
        print(' setting up subscription with callback to chassis at %s'%self.chassis)
        res = self.SetupSubscription()
        if res!=0: return res
        
        # and start the sever that waits for events
        print(' starting callback server at %s' % (self.callbackurl))
        print(' remember to allow port through windows firewall if applicable ...')
        
        res = self.StartServer(self.cbportno)
        return res


if __name__ == "__main__":
    demain = dllexpMain()
    sys.exit(demain.main())
    
    