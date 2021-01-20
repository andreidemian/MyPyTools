import os
class pidManager:
    """
    PID Manager, Creates a file with the pid of the curent running 
    script, also returns if the current stored pid is running
    
    Parameters:
    pid_file_path: path to file where pid will be stored
    """
    
    def __init__(self,pid_file_path="/var/run/mypid"):
        # Get PID
        self.PID = os.getpid()
        # Set the file path for pid storing
        self.PID_FILE = pid_file_path
        # set the file does not exists marker to False
        self.not_file = False
        # if the file does not exists create file and set PID
        if(not os.path.isfile(self.PID_FILE)):
            with open(self.PID_FILE, 'w') as wpidf:
                wpidf.write(str(self.PID))
            self.not_file = True
            
    # Get file stored pid
    @property        
    def getStoredPid(self):
        with open(self.PID_FILE, 'r') as rpidf:
           pid = rpidf.read()
        return int(pid)
    
    # Return if file stored pid is running
    def PS(self,pid):
        try:
            os.kill(pid, 0)
        except OSError:
            # pid is unassigned
            return False
        # pid is in use
        return True

    # Set pid if current file stored pid is not running and return 
    # False stored pid is running, True if stored pid is not running
    def setPid(self):
        """
        Parameters: setPid (): if the current stored pid is running returns False and exits,
        if the current stored pid si not running returns True and sets the new PID
        """
        if(self.not_file == True):
            # clear to start the app
            return True
        elif(self.PS(self.getStoredPid) == False):
            with open(self.PID_FILE,'w') as wfpid:
                wfpid.write(str(self.PID))
            # clear to start the app
            return True
        return False