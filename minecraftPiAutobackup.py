"""
MIT License

Copyright (c) 2023 Logan Herrera

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

@Author: Logan Herrera
@Date: 3/29/2023
@Python Version 3.92
@Purpose: The purpose of this python script is meant to be run as a cronjob 5 minutes before you want to set a
backup to automate the process of announcing to players that you will be backing up your server on the raspberry pi.
It is assumed that you will be creating a backup copy on the local machine but also transferring a full backup of that same file
to your NAS for robustness in case your microSD card on the pi dies out.
minecraftAutoBackup.py will first ssh into a remote server NAS host in this case 192.168.0.24 using an encrypted
id_rsa key with a password. Once it establishes a connection with the NAS, it
checks if your server is online via minestat by passing your info into minestat
and uses RCON to connect with console inside the server. It is also assumed you
have setup RCON with an RCON password via server.properties file in your minecraft server.
If minestat finds that your server is online it prepares for the backup announces to players
there will be a shutdown and then within 5 min shuts the server down, creates a tar.gz,
starts to transfer the backup after it is completed, and closes all connections, and then
it boots your server back up. In the event this script runs and minestat finds your server is
offline, then it will just boot the server up without doing anything else.
"""

import subprocess
import paramiko
import os
import glob
import sys
import time
from datetime import datetime, timedelta
import minestat
import tarfile
from mcrcon import MCRcon
import re
import stat
from tqdm import tqdm

#paths to remote and local directories of interest
r_path = '/home/pi/minecraftBackup'
l_path = '/home/pi/pythonscripts'

#Create Log file for paramiko ssh for debugging if needed
paramiko.util.log_to_file("paramiko.log")
#Define retention period default 7 days
retention = 7
#Get current date and time then cast to string
now = datetime.now()
retention_time = now - timedelta(days=retention)# Default set to days
timestamp = str(now.strftime("%Y%m%d_%H-%M-%S"))
#Create the backup file name
file_name = "My-Minecraft-Backup_"+timestamp+".tar.gz"

#Credentials maybe move this to a credentials file to be read in.
username = "pi"
host = "192.168.0.24"
port = 22
minecraft_port = 25565 #Java minecraft port
transport = paramiko.Transport((host,port)) #setup transport for put later
#Authenticate with remote NAS
mykey = paramiko.RSAKey.from_private_key_file("/home/pi/.ssh/id_rsa", password="Yourid_rsa_key_encryptedpasswordgoeshere")
print ("Connecting...")
transport.connect(username = username, pkey = mykey)#pass in key and connect
sftp = paramiko.SFTPClient.from_transport(transport)#setup sftp client
print ("Connected.")
#print (sftp.listdir()) #In case you want to list the directory Paramiko virtually 'sees' itself in

#Create Tar Function to create tar.gz file
def tardirectory(path,name):
    with tarfile.open(name, "w:gz") as tarhandle:
        for root, dirs, files in os.walk(path):
            for f in files:
                tarhandle.add(os.path.join(root,f))

#Countdown function To announce to Minecraft players via RCON that server will be shutting down once script is run
def countdown(aMcr):
    resp = aMcr.command("say Server will restart in 5 min. \n")
    time.sleep(240)#240 is 4 min
    resp = aMcr.command("say Server will restart in 1 min. \n")
    time.sleep(49)#49 to give 1 second extra time
    resp = aMcr.command("say Server will restart in... \n")
    count = 5 #for the below while loop to wait countdown for 5 seconds
    while(count != 0):
        resp = aMcr.command("say Timer Countdown %s " % (count))
        count-=1
        time.sleep(1)

####################### CAUTION #################################
#   Kept functions separate in case one wants to do something   #
#   different on local than on remote or vice versa             #
#   function to delete files after retention of x days          #
#                    default 7 days                             #
####################### CAUTION #################################
def delete_retention_local_files(retention_time, a_local_backuptargz_dir):
    search_tar = os.path.join(a_local_backuptargz_dir, '*.tar.gz')
    local_targzfiles = glob.glob(search_tar)
    for time_file in local_targzfiles:
        t_mod = os.path.getmtime(time_file)
        t_mod = datetime.fromtimestamp(t_mod)
        #print('{0} : {1}'.format(time_file, t_mod))
        if retention_time > t_mod:
            try:
                os.remove(time_file)#THE LOCAL TIME BOMB
                #print('Delete : Yes')
            except Exception:
                print('Delete : No')
                print('Error : {0}'.format(sys.exc_info()))
        else:
            pass
            #print('Delete : Not Required')

##################### CAUTION ###################################
# Paramiko glob and delete time bomb be very careful with this. #
# IT WILL DELETE REMOTE TAR.GZ files recursively! BE WARNED!    #
##################### CAUTION ###################################
def paramiko_glob_timebomb(path, pattern, sftp, retention_time):
    """
    Search recursively for files matching a given pattern.
    Parameters:
        path (str): Path to directory on remote machine.
        pattern (str): Python re [0] pattern for filenames.
        sftp (SFTPClient): paramiko SFTPClient.

    [0] https://docs.python.org/2/library/re.html
    credit to lkluft on the paramiko glob. Thank you!
    I tweaked it to do the removal of the timestamped files
    """
    p = re.compile(pattern)
    root = sftp.listdir(path)
    file_list = []

    # Loop over all entries in given path...
    for f in (os.path.join(path, entry) for entry in root):
        f_stat = sftp.stat(f)
        # ... if it is a directory call paramiko_glob recursively.
        if stat.S_ISDIR(f_stat.st_mode):
            file_list += paramiko_glob(f, pattern, sftp)
        # ... if it is a file, check the name pattern and append it to file_list.
        elif p.match(f):
            file_list.append(f)

    for rfiles in file_list:
        #print("looping over remote files " + rfiles)
        utime = sftp.stat(rfiles).st_mtime
        last_modified = datetime.fromtimestamp(utime)
        retention_time = now - timedelta(minutes=retention)
        if retention_time > last_modified:
            #print("Deleting the file " , last_modified)
            sftp.remove(rfiles) #THE REMOTE TIME BOMB
        else:
            pass
            #print("None passed Retention " , last_modified)
    return file_list

#Invoke Minestat to check if server is online then connect to MCRON use your own
#server info in the below strings to reflect your server
ms = minestat.MineStat('yourminecraftserveriporhostnameifyouhaveone', minecraft_port)
if ms.online:
    print("Minecraft server is online! \n")
    with MCRcon("localhost", "yourRConpassword") as mcr:
        resp = mcr.command("say Server is online running version %s with %s out of %s players. " % (ms.version, ms.current_players, ms.max_players))
        time.sleep(5)#give players a little extra time before server shutdown
        countdown(mcr)
        #Shut the server down via RCon Issuing 'stop' server command
        resp = mcr.command("stop")
        #resp = mcr.command("say pretending to stop server \n")
        print("stopped minecraft server. \n")
        time.sleep(200) #Give server time to shutdown and do its thing
	#Create tar calling tar function naming our backup filename My-Minecraft-Backup_timestamp.tar.gz
        #Show progress bar
        for i in tqdm(range(0,100), colour="#ed5c1a", desc ="Progress: "):
            tardirectory('/home/pi/minecraft/%s', file_name)
            sleep(.1)
        #change directory of remote server via paramiko point it to the path you want to store your backup in
        sftp.chdir(path=r_path)
        #Download get first part is path to local text file on remote sftp server path to the file you are trying to get.
        #Second part is the path to where you are putting the file locally where the python script is run
        #remotepath = '/home/pi/pythonscripts/%s'%file_name
        #mylocalpath = '/home/pi/minecraftBackup/%s'%file_name
        #sftp.get(remotepath, mylocalpath)
        #Upload put sends file from the pinecraft server aka mylocalpath to the remote server sftp via ssh aka remotepath which is a directory on the remote
        remotepath = '/home/pi/minecraftBackup/%s'%file_name #path to where you are putting the file on the NAS
        mylocalpath = '/home/pi/pythonscripts/%s'%file_name  #path to file you are wanting to transfer to the NAS
        print("Transferring backup to remote server... \n")
        sftp.put(mylocalpath, remotepath)#the actual upload command to transfer
        #Show progress bar as it Loops over list and delete files that surpass retention period
        #Start Local and Paramiko TimeBomb
        for i in tqdm(range(0,100), colour="#ed5c1a", desc ="Progress: "):
            delete_retention_local_files(retention_time, l_path)
            NAS_files = paramiko_glob_timebomb(r_path, '.*\.tar.gz', sftp, retention_time)
            sleep(.1)
        print(NAS_files)
        #Close connections
        sftp.close()
        transport.close()
        tarfile.close()
        print ("File securely copied to remote server. Closed connection.\n")
	#File backed up and now we Boot the minecraft server back up with screen using subprocess then detaching
        proc = subprocess.Popen(["screen -dmS minecraft ~/minecraft/server"], shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        print("Server Booting back up. \n")
else:
    print("Server Offline! Booting up server now. \n ")#Else server was never online to begin with so start it up
    proc = subprocess.Popen(["screen -dmS minecraft ~/minecraft/server"], shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    print("Server Starting up... \n")

print ("Ending Program.")#end program
