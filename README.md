# piautobackup-minecraft
Raspberry Pi Autobackup for Minecraft server with NAS backup
I am creating this project to allow whoever is hosting a Minecraft game server,
the ability to automate the process of warning players that the server will be brought down for creating backups,
sftp the backup over to a remote NAS, and rebooting the server. This will all be done with the ease of mind knowing your backup
is safe, not only on your local machine, but also on a remote NAS, that you host as well.
All are welcome to help me make this more efficient and better as it evolves.
Thank you and I hope it works for you all! Pretty cool site that explains what each asterisk means. https://crontab.guru/#*_*_*_*_*

***
Instructions for setting up a cronjob Python Script via crontab in the Linux Environment: Python version:3.92
***

**1. Open Linux Terminal.**

**2. Type 'crontab -e' to create crontab.**

**3. Press 'i' to launch edit mode.**

**4. Type the schedule command ' * * * * * /usr/bin/python /path/to/file/minecraftPiAutobackup.py; '**

**5. Press 'esc' to exit edit mode.**

**6. Type ' :wq ' to write your crontab.**

**7. To delete the running job:**
    **To delete the entire crontab: Run 'crontab -r'**
    **To delete a single cron job: Go to 'crontab -e' , press 'i' , press 'dd' and press ' :wq ' to write the file.**
