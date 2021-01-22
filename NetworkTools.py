import os
import socket
import platform
from subprocess import Popen, PIPE, call
import re
class NetworkTools:
    
    def __init__(self,host="192.168.1.1",file_path=None):
        self.host = host
        self.os_type = platform.system().lower()
        self.cur_path = os.path.dirname(os.path.realpath(__file__))
        if(file_path):
            self.cur_path = file_path
        
    def __run(self,cmd):
        pp = Popen(cmd,shell=True,stdout=PIPE,stderr=PIPE)
        stdout,stderr = pp.communicate()
        return stdout, stderr

    def fileList(self,flist):
        dir_list = []
        if(os.path.isfile(flist)):
            with open(flist,'r') as file_r:
                for i in file_r:
                    line = i.strip()
                    gm = re.search(r'^#',line)
                    if(not gm):
                        dir_list.append(line)
        return dir_list

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
    
    def dnsbl(self):
        ValidIpAddressRegex = "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$";
        #ValidHostnameRegex = "^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$";
        ## IPV4
        ipre = re.search(r'{}'.format(ValidIpAddressRegex),
                         self.host)
        if(ipre):
            ipv4 = self.host.split('.')
        else:
            ipv4 = socket.gethostbyname(self.host).split('.')
            
        rip = '{3}.{2}.{1}.{0}'.format(ipv4[0],ipv4[1],ipv4[2],ipv4[3])
        dnsbl_list = self.fileList(os.path.join(self.cur_path,'dnsbl.list'))

        dnsbl_result = []
        count = 0
        for i,dnsbl in enumerate(dnsbl_list):
            dnsbl_str = '{rip}.{dnsbl}'.format(rip=rip,dnsbl=dnsbl)
            dnsbl_result.append({'dnsbl':dnsbl,'host':self.host,'ipv4':ipv4,'result':None,'listed':None})
            try:
                response = socket.gethostbyname(dnsbl_str)
                dnsbl_result[i]['result'] = response
                dnsbl_result[i]['listed'] = True
                count = count + 1
            except:
                dnsbl_result[i]['listed'] = False
        #return dnsbl_result
        print(count)
        return dnsbl_result

test = NetworkTools('172.21.34.3').dnsbl()
for i in test:
    print(i)