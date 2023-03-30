"""
@Author: Logan Herrera
@Date: 3/29/2023
@Python Version 3.92
@Purpose: The purpose of this python script is meant to be run as a cronjob 5 minutes before you want to set a 
backup to automate the process of announcing to players that you will be backing up your server on the raspberry pi.
It is assumed that you will be creating a backup copy on the local machine but also transferring a full backup of that same file 
to your NAS for robustness in case your microSD card on the pi dies out. 
minecraftAutoBackup.py will first ssh into a remote server NAS host in this case 192.168.0.24 using an encrypted
id_rsa key with a password.
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
#Credentials maybe move this to a credentials file to be read in.
username = "pi"
host = "192.168.0.24"
port = 22
minecraft_port = 25565 #Java minecraft port
transport = paramiko.Transport((host,port))
#Authenticate with remote NAS
mykey = paramiko.RSAKey.from_private_key_file("/home/pi/.ssh/id_rsa", password="Yourid_rsa_key_encryptedpasswordgoeshere")
print ("Connecting...")
transport.connect(username = username, pkey = mykey)
sftp = paramiko.SFTPClient.from_transport(transport)
print ("Connected.")
#print (sftp.listdir()) #In case you want to list the directory Paramiko virtually 'sees' itself in