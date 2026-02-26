# ⛏️ Raspberry Pi Minecraft Auto-Backup

A robust Python automation tool for Minecraft servers hosted on Raspberry Pi. This script streamlines the maintenance window by warning players, creating compressed backups, syncing to a remote NAS via SFTP, and managing server reboots.

## 🚀 Features

- **Player Notifications:** Sends automated warnings to the server chat before maintenance starts.
- **Dual-Layer Backup:** Generates local `.tar.gz` archives and mirrors them to a remote NAS via SFTP.
- **Smart Cleanup:** Automatically manages storage by deleting old backups (recursively) on both local and remote machines.
- **Cron Integration:** Optimized for headless execution via crontab.

## ⚠️ IMPORTANT: Data Safety Warning

> [!CAUTION]
> This software is designed to manage storage by recursively deleting `.tar.gz` files in your specified backup directories.
>
> Double-check your paths! If your backup path is set to a directory containing other important archives, they may be lost. Use at your own risk.

## 📋 Prerequisites

- **Python:** 3.9.2 or higher.
- **SSH/SFTP:** Ensure you have network access and credentials for your remote NAS.
- **Server Access:** The script needs permissions to execute commands and access the Minecraft server directory.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Loksta8/piautobackup-minecraft.git
cd piautobackup-minecraft
```

2. Install required dependencies:

```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

The script relies on a `config.json` file for server and NAS credentials.

1. **Edit `config.json`:** Enter your specific server IP, port, login credentials, and folder paths.
2. **SSH Key Passphrase:** If you use an encrypted SSH key, open `minecraftPiAutobackup.py` and enter your passphrase in the designated variable.

> **Note:** If you prefer not to use a config file, you can hardcode your defaults directly into the Python script.

## 🛠️ Usage

### Manual Execution

To run a backup immediately using your config file:

```bash
python minecraftPiAutobackup.py --config config.json
```

### Scheduling with Crontab

To automate your backups (e.g., every day at 3:00 AM):

1. Open the crontab editor:

```bash
crontab -e
```

2. Enter Insert Mode (press `i`).

3. Add your schedule line:

```
0 3 * * * /usr/bin/python3 /full/path/to/minecraftPiAutobackup.py --config /full/path/to/config.json
```

> Not sure about the timing? Use [crontab.guru](https://crontab.guru) to experiment with schedules.

4. **Save and Exit:** Press `Esc`, type `:wq`, and hit `Enter`.

### Managing the Job

- **View running jobs:** `crontab -l`
- **Delete all jobs:** `crontab -r`
- **Delete one job:** Edit with `crontab -e`, delete the specific line, and save.

## 🤝 Contributing

Contributions make the open-source community an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
