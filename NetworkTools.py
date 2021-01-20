import os
import socket
import platform
from subprocess import Popen, PIPE, call
import re
class NetworkTools:
    
    def __init__(self,host="192.168.1.1"):
        self.host = host
        self.os_type = platform.system().lower()
        
    def __run(self,cmd):
        pp = Popen(cmd,shell=True,stdout=PIPE,stderr=PIPE)
        stdout,stderr = pp.communicate()
        return stdout, stderr
        
    def portisopen(self,port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        try:
            s.connect((self.host, int(port)))
            s.shutdown(2)
            return True
        except:
            return False
        
    def ping(self,count='1'):
        ### windows
        if(self.os_type == 'windows'):
            ping = 'ping -n {} {}'.format(count,self.host)
            stdout, stderr = self.__run(ping)
            if(not stderr):
                rez = re.search(r'Lost = 0',stdout.decode('utf-8'))
                if(rez):
                    return True
        ### linux
        elif(self.os_type == 'linux'):
            ping = 'ping -c {} {}'.format(count,self.host)
            stdout, stderr = self.__run(ping)
            if(not stderr):
                rez = re.search(r'received, 0% packet loss',stdout.decode('utf-8'))
                if(rez):
                    return True
        return False
        