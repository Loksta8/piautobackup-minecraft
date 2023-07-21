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
@Date: Updated on 7/20/2023
@Python Version 3.92
@Purpose: The purpose of this python script is meant to be run as a cronjob 5 minutes before you want to set a
backup to automate the process of announcing to players in game that you will be backing up your server on the raspberry pi.
It is assumed that you will be creating a backup copy on the local machine but also transferring a full backup of that same file
to your NAS for robustness in case your microSD card on the pi dies out. minecraftAutoBackup.py will first ssh into a remote
server NAS host in this case 192.168.0.24 using an encrypted id_rsa key with a password. Once it establishes a connection with
the NAS, it checks if your server is online via minestat by passing your info into minestat and uses RCON to connect with console
inside the server. It is also assumed you have setup RCON with an RCON password via server.properties file in your minecraft server.
If minestat finds that your server is online it prepares for the backup announces to players there will be a shutdown and then
within 5 min shuts the server down, creates a tar.gz, starts to transfer the backup after it is completed, and closes all
connections, and then it boots your server back up. In the event this script runs and minestat finds your server is offline,
then it will just boot the server up and delete any backups that are on the local and remote machines passed the retention period.
I updated this script to be in Object Oriented Programming form and to ingest a JSON config file. I took out the comments from
before since I tried to make the code more readable through functions. I am open to any feedback on how to make this code better.
Thank you and I hope this helps some self hosting gamers out there!
"""

import subprocess
import paramiko
import os
import glob
import time
import logging
import json
from datetime import datetime, timedelta
import minestat
import tarfile
from mcrcon import MCRcon
import re
import stat
from tqdm import tqdm
import argparse

class MinecraftBackup:
    def __init__(self, config):
        self.config = config
        self.transport = None
        self.sftp = None

    def connect(self):
        try:
            logging.info("Connecting...")
            self.transport = paramiko.Transport((self.config["host"], self.config["port"]))
            mykey =
            paramiko.RSAKey.from_private_key_file(self.config["private_key_path"],password="yourRSAkeyPasswordGoesHere!")
            self.transport.connect(username=self.config["username"], pkey=mykey)
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)
            logging.info("Connected.")
        except Exception as e:
            logging.error(f"Error connecting: {e}")
            raise

    def disconnect(self):
        try:
            self.sftp.close()
            self.transport.close()
            logging.info("Disconnected.")
        except Exception as e:
            logging.error(f"Error disconnecting: {e}")

    def tar_directory(self, path, name):
        with tarfile.open(name, "w:gz") as tarhandle:
            tarhandle.add(path, recursive=True)

    def countdown(self, aMcr):
        try:
            resp = aMcr.command("say Server will restart in 5 min.\n")
            time.sleep(240)  # 240 is 4 min
            resp = aMcr.command("say Server will restart in 1 min.\n")
            time.sleep(49)  # 49 to give 1 second extra time
            resp = aMcr.command("say Server will restart in...\n")
            for count in reversed(range(1, 6)):
                resp = aMcr.command(f"say Timer Countdown {count}\n")
                time.sleep(1)
        except Exception as e:
            logging.error(f"Error during countdown: {e}")

    def delete_retention_local_files(self, retention_time):
        try:
            search_tar = os.path.join(self.config["local_path"], '*.tar.gz')
            local_tar_files = glob.glob(search_tar)
            files_to_delete = []
            for time_file in local_tar_files:
                t_mod = os.path.getmtime(time_file)
                t_mod = datetime.fromtimestamp(t_mod)
                if retention_time > t_mod:
                    files_to_delete.append(time_file)

            if files_to_delete:
                for file_to_delete in files_to_delete:
                    os.unlink(file_to_delete)
                logging.info(f"Deleted {len(files_to_delete)} local retention files.")
        except Exception as e:
            logging.error(f"Error deleting local retention files: {e}")

    def delete_remote_retention_files(self, retention_time):
        try:
            p = re.compile('.*\.tar.gz')
            files_to_delete = []

            def process_files(path, files):
                for file in files:
                    file_path = os.path.join(path, file)
                    f_stat = self.sftp.stat(file_path)
                    if stat.S_ISDIR(f_stat.st_mode):
                        subpath = os.path.join(path, file)
                        subfiles = self.sftp.listdir(subpath)
                        process_files(subpath, subfiles)
                    elif p.match(file):
                        utime = f_stat.st_mtime
                        last_modified = datetime.fromtimestamp(utime)
                        if retention_time > last_modified:
                            files_to_delete.append(file_path)

            process_files(self.config["remote_path"], self.sftp.listdir(self.config["remote_path"]))

            if files_to_delete:
                for file_to_delete in files_to_delete:
                    self.sftp.remove(file_to_delete)
                logging.info(f"Deleted {len(files_to_delete)} remote retention files.")
        except Exception as e:
            logging.error(f"Error deleting remote retention files: {e}")

    def backup_minecraft_server(self, timestamp):
        ms = minestat.MineStat(self.config["minecraft_server_ip"], self.config["minecraft_server_port"])
        if ms.online:
            logging.info("Minecraft server is online!")
            with MCRcon("localhost", self.config["rcon_password"]) as mcr:
                resp = mcr.command("say Server is online running version %s with %s out of %s players. " % (
                    ms.version, ms.current_players, ms.max_players))
                time.sleep(5)
                self.countdown(mcr)
                resp = mcr.command("stop")
                logging.info("Stopped Minecraft server.")
                time.sleep(200)
                self.create_tar_backup(timestamp)
                self.transfer_backup_to_remote(timestamp)
                logging.info("File securely copied to remote server. Closed connection.")
                self.start_minecraft_server()
        else:
            logging.info("Server Offline! Booting up the server now.")
            self.start_minecraft_server()
            logging.info("Server Starting up.")

    def create_tar_backup(self, timestamp):
        try:
            logging.info("Creating tar backup...")
            tar_file_path = os.path.join(self.config["local_path"], f"My-Minecraft-Backup_{timestamp}.tar.gz")

            # Count the total number of files for progress bar
            total_files = 0
            for root, _, files in os.walk('/home/pi/minecraft'):
                total_files += len(files)

            with tqdm(total=total_files, colour="#ed5c1a", desc="Progress", unit="file") as progress_bar:
                with tarfile.open(tar_file_path, "w:gz") as tarhandle:
                    for root, dirs, files in os.walk('/home/pi/minecraft'):
                        for file in files:
                            file_path = os.path.join(root, file)
                            tarhandle.add(file_path)
                            progress_bar.update(1)

            logging.info(f"Tar backup created: {tar_file_path}")
        except Exception as e:
            logging.error(f"Error creating tar backup: {e}")
            raise

    def transfer_backup_to_remote(self, timestamp):
        try:
            logging.info("Transferring backup to remote server...")
            remote_path = os.path.join(self.config["remote_path"], f"My-Minecraft-Backup_{timestamp}.tar.gz")
            local_path = os.path.join(self.config["local_path"], f"My-Minecraft-Backup_{timestamp}.tar.gz")
            self.sftp.put(local_path, remote_path)
            logging.info(f"Backup transferred to remote server: {remote_path}")
        except Exception as e:
            logging.error(f"Error transferring backup to remote server: {e}")
            raise

    def start_minecraft_server(self):
        try:
            proc = subprocess.Popen(["screen -dmS minecraft ~/minecraft/server"], shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
            logging.info("Server Booting back up.")
        except Exception as e:
            logging.error(f"Error starting Minecraft server: {e}")

    def run(self):
        try:
            self.connect()
            now = datetime.now()
            retention_time = now - timedelta(days=self.config["retention_days"])
            timestamp = now.strftime("%Y%m%d_%H-%M-%S")
            self.backup_minecraft_server(timestamp)
            self.delete_retention_local_files(retention_time)
            self.delete_remote_retention_files(retention_time)
        except Exception as e:
            logging.error(f"Error during backup process: {e}")
        finally:
            self.disconnect()
            logging.info("Ending Program.")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Minecraft Server Backup Script")
    parser.add_argument("--config", "-c", type=str, help="Path to the config file")
    args = parser.parse_args()
    return args

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("minecraft_backup.log"),
            logging.StreamHandler()
        ]
    )

def load_config(file_path):
    try:
        with open(file_path, "r") as config_file:
            config = json.load(config_file)
        return config
    except Exception as e:
        logging.error(f"Error loading config file: {e}")
        raise

if __name__ == "__main__":
    args = parse_arguments()

    setup_logging()
    logging.info("Starting Minecraft server backup...")

    if args.config:
        config = load_config(args.config)
    else:
        # Default configuration if no config file provided
        config = {
            "host": "192.168.0.24",
            "port": 22,
            "username": "pi",
            "private_key_path": "/home/pi/.ssh/id_rsa",
            "remote_path": "/home/pi/minecraftBackup",
            "local_path": "/home/pi/pythonscripts",
            "minecraft_server_ip": "yourminecraftserverIPorhostnameifyouhaveone",
            "minecraft_server_port": 25565,
            "rcon_password": "putyourRConpassword",
            "retention_days": 7
        }

    backup = MinecraftBackup(config)
    backup.run()
