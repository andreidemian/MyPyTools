import os
import socket
import platform
from subprocess import Popen, PIPE
import re
import queue
import concurrent.futures

class NetworkTools:
    """
    NetworkTools package 
    Available methods:
        - runCmd(cmd)  -- run command on system
        - OpenPort(host,port) -- check if port is open on target host
        - ping(host,count=1) -- check if ping works on host
    """
    def __init__(self):
        self.os_type = platform.system().lower()
        self.cur_path = os.path.dirname(os.path.realpath(__file__))
        
    def runCmd(self,cmd):
        ## run commands on system
        pp = Popen(cmd,shell=True,stdout=PIPE,stderr=PIPE)
        stdout,stderr = pp.communicate()
        return stdout, stderr

    def OpenPort(self,host,port):
        ## check if port is open on target host
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        try:
            s.connect((host, int(port)))
            s.shutdown(2)
            return True
        except:
            return False
     
    def ping(self,host,count='1'):
        ## send icmp request on target host
        ### windows
        if(self.os_type == 'windows'):
            ping = 'ping -n {} {}'.format(count,host)
            stdout, stderr = self.runCmd(ping)
            if(not stderr):
                dhu = re.search(r'Destination host unreachable',stdout.decode('utf-8'))
                lost = re.search(r'Lost = 0',stdout.decode('utf-8'))
                if(lost and not dhu):
                    return True
        ### linux
        elif(self.os_type == 'linux'):
            ping = 'ping -c {} {}'.format(count,host)
            stdout, stderr = self.runCmd(ping)
            if(not stderr):
                rez = re.search(r'received, 0% packet loss',stdout.decode('utf-8'))
                if(rez):
                    return True
        return False

class DNSBlackList(NetworkTools):
    
    """
    DNSBlackList can be used to check via DNS if IPv4 is black listed
    Parameters:
    file_path: path to dnsbl list, if no path is set, default path is same location as the script
    host: IPv4 or HostName to check against the dnsbl list
    """
    
    def __init__(self,file_path=None,host='192.168.1.1'):
        super().__init__()
        self.host = host
        if(file_path):
            self.cur_path = file_path
    
    def fileList(self,flist):
        ## Collect DNSBL domains from txt file
        Q = queue.Queue()
        if(os.path.isfile(flist)):
            with open(flist,'r') as file_r:
                for i in file_r:
                    line = i.strip()
                    gm = re.search(r'^#',line)
                    if(not gm):
                        Q.put(line)
        return Q
    
    def DNSBL(self,dnsbl,host):
        
        ## check if host or IPv4 if blacklisted
        
        dnsbl_result = []
        
        # Regex for IP validation
        ValidIpAddressRegex = "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$";
        
        ## if not IP then dns lookup to return the IP
        ipre = re.search(r'{}'.format(ValidIpAddressRegex),host)
        if(ipre):
            ipv4 = host.split('.')
        else:
            ipv4 = socket.gethostbyname(host).split('.')

        ## revese the IP for dns check
        rip = '{3}.{2}.{1}.{0}'.format(ipv4[0],ipv4[1],ipv4[2],ipv4[3])
        
        dnsbl_str = '{rip}.{dnsbl}'.format(rip=rip,dnsbl=dnsbl)
        dnsbl_result = {'dnsbl':dnsbl,
                        'host':host,
                        'ipv4':ipv4,
                        'result':None,
                        'listed':None}
        try:
            response = socket.gethostbyname(dnsbl_str)
            dnsbl_result['result'] = response
            dnsbl_result['listed'] = True
        except:
            dnsbl_result['listed'] = False

        return dnsbl_result
    
    def run(self):

        ## Create threads and checking host or IPv4 against all the DNSBL domains
        
        dnsbl_list = self.fileList(os.path.join(self.cur_path,'dnsbl.list'))
        threads = []
        dnsbl_result = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            while(not dnsbl_list.empty()):
                threads.append(executor.submit(self.DNSBL, dnsbl=dnsbl_list.get(), host=self.host))
            for thread in concurrent.futures.as_completed(threads):
                dnsbl_result.append(thread.result())
        return dnsbl_result
   
class RouteTable(NetworkTools):
    def __init__(self):
        super().__init__()
        
    def CheckRT(self,route):
        stdout, stderr = self.runCmd('ip -d route show')
        rez = re.search(r'{}'.format(route),stdout.decode('utf-8'))
        if(rez):
            return True
        return False
    
    def addDefaultGw(self,gw,dev=None):
        if(not self.CheckRT('default via {}'.format(gw))):
            if(dev):
               self.runCmd('ip route add default via {} dev {}'.format(gw,dev))
            else:
                self.runCmd('ip route add default via {}'.format(gw))