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
import time
import datetime
import minestat
import tarfile
from mcrcon import MCRcon

#Create Log file for paramiko ssh for debugging if needed
paramiko.util.log_to_file("paramiko.log")
#Get current date and time then cast to string
now = datetime.datetime.now()
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
        tardirectory('/home/pi/minecraft/%s', file_name)
        #change directory of remote server via paramiko point it to the path you want to store your backup in
        sftp.chdir(path='/home/pi/minecraftBackup')
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
