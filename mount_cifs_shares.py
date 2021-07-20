#!/usr/bin/python3

from subprocess import Popen, PIPE
import os
import re
import sys
import socket
from datetime import datetime
import getpass


# If you have a SMB server with a interface in each vlan 
#you can add the ip of each vlan interface, and the script will choose the ip 
#that is in the same vlan as the computer you are running the script from

CIFS_SHARES = {
                "share$":["192.168.1.10","192.168.2.10"],
                "share2$":["192.168.1.10","192.168.2.10"]
}


# If the computer from which you are running the script is not in any VLANs with the SMB server
#a default ip that can be used to reach the SMB server
DEFAULT_SMB_IP = "192.168.0.10"

# Directory where all the mount points are created
MOUNT_DST = "/mnt"

### Linux User ID - if None you will be prompted to enter the UID (this is preferred)
LINUX_UID = None
### Linux Group ID - if None you will be prompted to enter the GID (this is preferred)
LINUX_GID = None
### file mode
LINUX_FILE_MODE = "0660"
### Directory mode
LINUX_DIR_MODE = "0770"
### SMB User - if None you will be prompted to enter the SMB User (this is preferred)
SMB_USER=None
### SMB Password - if None you will be prompted to enter the SMB Password (this is preferred)
SMB_PASS=None
### SMB DOMAIN - if None you will be prompted to enter the SMB DOMAIN
SMB_DOMAIN="domain.local"
### SMB port
SMB_PORT=445
### SMB version
SMB_VERSION="3.0"

### Don't change this params !
SCRIPT_DIR=os.path.dirname(os.path.realpath(__file__))
SCRIPT_PATH=os.path.join(os.path.dirname(os.path.realpath(__file__)),sys.argv[0])

### Credentials file Path
CREDENTIAL_FILE = os.path.join(SCRIPT_DIR,".cifs.cre")

######################################################################################################
######################################################################################################

def run(cmd):
    rp = Popen(cmd,shell=True,stdout=PIPE,stderr=PIPE)
    stdout,stderr = rp.communicate()
    return stdout, stderr

def isOpen(ip,port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except:
        return False

def check_UID_GID(G_U_ID="UID",ID="root"):
    if(G_U_ID == "UID"):
        with open("/etc/passwd","r") as passwd_f:
            for line in passwd_f:
                if(re.search(r'{}'.format(ID),line)):
                    return True
    if(G_U_ID == "GID"):
        with open("/etc/group","r") as passwd_f:
            for line in passwd_f:
                if(re.search(r'{}'.format(ID),line)):
                    return True
    return False

def credential_manager(reset_cred=False):
    
    global CREDENTIAL_FILE

    if(not os.path.isfile(CREDENTIAL_FILE) or reset_cred):
        global SMB_DOMAIN
        global SMB_USER
        global SMB_PASS
        global LINUX_UID
        global LINUX_GID
        
        print("\n-------------------------- Set the SMB credentials and Linux UID and GID --------------------------\n")
        
        if(SMB_DOMAIN == None):
            SMB_DOMAIN = str(input('DOMAIN: '))
        if(SMB_USER == None):
            SMB_USER = str(input('DOMAIN USERNAME: '))
        if(SMB_PASS == None):
            SMB_PASS = getpass.getpass('DOMAIN PASSWORD: ')
        
        if(LINUX_UID == None):
            LINUX_UID = str(input('LINUX USER ID: '))
        if(LINUX_GID == None):
            LINUX_GID = str(input('LINUX GROUP ID: '))

        credentials = """uid={uid}
gid={gid}
domain={domain}
username={user}
password={password}
""".format(uid=LINUX_UID,
            gid=LINUX_GID,
            domain=SMB_DOMAIN,
            user=SMB_USER,
            password=SMB_PASS)

        with open(CREDENTIAL_FILE, 'w') as w_c_f:
            w_c_f.write(credentials)
            
        os.chmod(CREDENTIAL_FILE, 0o600)
        
    with open(CREDENTIAL_FILE,'r') as r_c_f:
        for line in r_c_f:
            if('uid=' in line):
                LINUX_UID = line.strip().split("=")[1]
            if('gid=' in line):
                LINUX_GID = line.strip().split("=")[1]

    exit_if_UID_OR_GID = False
    if(not check_UID_GID(G_U_ID="UID", ID=LINUX_UID)):
        print("\n Specified Linux User-ID \"{}\" does not exist\n".format(LINUX_UID))
        exit_if_UID_OR_GID = True
    if(not check_UID_GID(G_U_ID="GID",ID=LINUX_GID)):
        print("\n Specified Linux Group-ID \"{}\" does not exist\n".format(LINUX_GID))
        exit_if_UID_OR_GID = True

    if(exit_if_UID_OR_GID):
        if(os.path.isfile(CREDENTIAL_FILE)):
            os.remove(CREDENTIAL_FILE)
        sys.exit(1)

def check_mount_point(mount_point):
    stdout,stderr = run('mount')
    if(re.search(r'{}'.format(mount_point),stdout.decode('UTF-8'))):
        return True
    return False

def cifs_umount(mount_point):
    print_msg = ""
    
    mck = check_mount_point(mount_point)
    if(mck):
        run('umount {}'.format(mount_point))
        mck = check_mount_point(mount_point)
        if(mck == False):
            print("\n \"{}\" Successfuly unmounted ".format(mount_point))
        else:
            print("\n Failed to unmount \"{}\"".format(mount_point))
    else:
        print("\n Nothing is mounted on \"{}\"".format(mount_point))

    return mck
        
def cifs_mount(smb_host,smb_port,share,mount_point):
    if(os.path.isdir(mount_point)):
        run('mount -t cifs -o vers={vers},credentials={credentials},uid="{uid}",gid="{gid}",file_mode="{file_mode}",dir_mode="{dir_mode}",port={port} //{host}/{msrc} {mdst}'.format(
            uid=LINUX_UID,
            gid=LINUX_GID,
            file_mode=LINUX_FILE_MODE,
            dir_mode=LINUX_DIR_MODE,
            host=smb_host,
            msrc=share,
            mdst=mount_point,
            port=smb_port,
            credentials=CREDENTIAL_FILE,
            vers=SMB_VERSION
        ))
    mck = check_mount_point(mount_point)
    if(mck):
        print("\n \"{}\" Successfuly mounted".format(share))
        return mck
    print("\n \"{}\" Mount failed".format(share))
    return mck

def netwok_interface_ip(IP="192.168.123.1"):
    ## remove host digits from IP
    remove_host_from_IP = re.search(r'[0-9]+\.[0-9]+\.[0-9]+',IP)
    IP = remove_host_from_IP.group(0)
    #print(IP)
    ## retrive interface ip
    stdout, stderr = run("ip address show")
    IPv4 = []
    for line in stdout.decode('UTF-8').split('\n'):
        inte_search = re.search(r'[0-9]+\.[0-9]+\.[0-9]+',line)
        if(inte_search):
            IP_i = inte_search.group(0)
            if (IP_i not in ('0.0.0','255.255.255','127.0.0')):
                IPv4.append(IP_i)
    #print(IPv4)
    ## check if host net maches the any of the interface IP
    if(IP in IPv4):
        return True
    return False
        
def prompt_for_yes_no(question, default="yes"):

    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n]: "
    elif default == "yes":
        prompt = " [Y/n] Default is Yes: "
    elif default == "no":
        prompt = " [y/N] Default is No: "
    else:
        raise ValueError("\n invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("\n Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")

def main(umount_exit=False):
    for share,IPs in CIFS_SHARES.items():
        use_this_ip = DEFAULT_SMB_IP
        for IP in IPs:
            if(netwok_interface_ip(IP)):
                use_this_ip = IP
                break
        
        ### create mount-point directory
        mount_point = share.replace('$','')
        mnt_dst_full_path = os.path.join(MOUNT_DST,mount_point)
        #print(mnt_dst_full_path)
        
        if(umount_exit):
            cifs_umount(mnt_dst_full_path)
            continue
        
        if(not os.path.isdir(mnt_dst_full_path)):
            print("\n Creating mount point directory for share \"{}\" in \"{}\", fullpath: \"{}\"".format(share,MOUNT_DST,mnt_dst_full_path))
            os.mkdir(mnt_dst_full_path)
        
        if(isOpen(use_this_ip,SMB_PORT)):
            ## check if mount potin is already in use by other mount and ask to unmount 
            mount_point_status = True
            if(check_mount_point(mnt_dst_full_path)):
                umount_res = prompt_for_yes_no(question="\n Mount point \"{}\" already in use\n would you like to unmount the existing mount point\n and continue with the new mount ?".format(mnt_dst_full_path),default="no")
                if(umount_res):
                    cifs_umount(mnt_dst_full_path)
                else:
                    mount_point_status = False
                    
            ## Mount share
            if(mount_point_status):
                cifs_mount(use_this_ip,SMB_PORT,share,mnt_dst_full_path)
                print("\n Share \"{}\" using smb host ip \"{}\"\n".format(share,use_this_ip))
            else:
                print("\n Skipping share \"{}\" mount point \"{}\" already in use\n".format(share,mnt_dst_full_path))
            
        else:
            print("\n NO SMB Host for share \"{}\" is listening on the specified IP \"{}\"".format(share,use_this_ip))
            
### Run script
if(os.geteuid() == 0):
    if(not os.path.isfile("/sbin/mount.cifs")):
        print("\n WARNING ! cifs-utils is not available, please install cifs-utils package")
    
    reset_cred = False
    umount = False
    if(len(sys.argv)>1):
        
        reset_ref = ['set','--set','reset','--reset','-r']
        umount_ref = ['umount','--umount','-u']
    
        if(sys.argv[1].lower() in reset_ref):
            reset_cred = True
        elif(sys.argv[1].lower() in umount_ref):
            umount = True
        else:
            print("\n------------------------------------------ {} help ------------------------------------------\n".format(sys.argv[0]))
            print("\n")
            print(" -- \"sudo python3 {}\" - Mount shares\n".format(sys.argv[0]))
            print(" -- \"sudo python3 {} reset\" - Reset credentials and mount shares\n".format(sys.argv[0]))
            print(" -- \"sudo python3 {} umount\" - Umount shares\n".format(sys.argv[0]))
            print("------------------------------------------------------------------------------------------------------------------\n")
            sys.exit(0)

    credential_manager(reset_cred)
    main(umount)
else:
    sys.exit("\n -------------- YOU NEED TO RUN THE SCRIPT WITH \"SUDO\" OR FROM THE \"ROOT\" ACCOUNT ! ------------------------\n")