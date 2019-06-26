"""

 Sample Python wrapper for test_dll.DLL
 
 (c) Xena Networks 2019

"""

from ctypes import *


class TestDll():
    
    def loaddll(self,dllfile='TEST.DLL'):
        # replace name with real dll file name and uncomment next line
        #self.dll = cdll.LoadLibrary(dllfile)
        pass 
         
    
        
    def CheckSerial(self,user='',serial=''):
        pms = [user,serial]
        print ('CheckSerial(%s)'%pms)
        """
          replace the lines below with real calls to DLL functions of the loaded dll
          this version just fails if the serial is empty
        """
        if len(serial)==0:
            res = (1, 'Serial number check failed, serial is empty')
        else:
            res = (0, 'Serial number %s passed check and is valid'%serial)
    
        print ('CheckSerial result -> %s %s'%res)
        return res
    
    def WriteTestData (self,user='',serial='', result='',testlog=''):
        pms = [user,serial,result,testlog]
        print ('WriteTestData(%s)'%pms)
        
        """
          replace the lines below with real calls to DLL functions of the loaded dll
          this version just fails if the serial is empty
        """
        if len(serial)==0:
            res = (1, 'Storage of test result %s failed, serial is empty'%result)
        else:
            res = (0, 'Storage of test result %s for serial %s was successful'%(result,serial))
        
        
        print ('WriteTestData result -> %s %s'%res)
        return res
 
 
    