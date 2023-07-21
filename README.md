# piautobackup-minecraft
Raspberry Pi Autobackup for Minecraft server with NAS backup
I am creating this project to allow whoever is hosting a Minecraft game server,
the ability to automate the process of warning players that the server will be brought down for creating backups,
sftp the backup over to a remote NAS, and rebooting the server. This will all be done with the ease of mind knowing your backup
is safe, not only on your local machine, but also on a remote NAS, that you host as well.
All are welcome to help me make this more efficient and better as it evolves.
Thank you and I hope it works for you all! Pretty cool site that explains what each asterisk means. https://crontab.guru/#\*_\*_\*_\*_\*\

> ***Instructions for setting up a cronjob Python Script via crontab in the Linux Environment: Python version:3.92***

> :warning: **Warning:**
>
> ***This software when run will delete .tar.gz files recursively if paths point to
> directories within other directories. Make sure you don't have anything worth
> losing. Deletion happens on your local machine and on your remote machine! Use
> at your own risk!***

> 📔 **Note:**
> 
> First you must enter your server info in the `config.json` and if you have an ssh key password enter that in `minecraftPiAutobackup.py` file.
> If you don't want to use a config file, enter your own server and ssh password information in the `minecraftPiAutobackup.py` script instead and it will be the default.


**1. Open Linux Terminal.**

**2. Type below to create crontab.**

`crontab -e`

**3. Press below to launch edit mode.**

`i`

**4. Setup the time you want the crontab to schedule itself using the below command.**

` * * * * * /usr/bin/python /path/to/file/minecraftPiAutobackup.py;`

**5. Press the escape key to exit edit mode.**

`esc`

**6. Type the below command to write your crontab.**

`:wq`

**7. To delete the running job:**

**To delete the entire crontab: Run:**

`crontab -r`

**To delete a single cron job: Do the follow below to edit, delete, then write the file.**

`crontab -e`

`i`

`dd`

`:wq`
