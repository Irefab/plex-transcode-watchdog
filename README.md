# plex-transcode-watchdog

A lightweight Python script that polls your Plex server and logs active sessions,
highlighting whether each stream is **Direct Play**, **Direct Stream**, or **Transcoding**.
Use it to spot devices that force transcodes (e.g., 4K HDR to 1080p SDR), track buffering hotspots,
and guide fixes (client settings, codecs, network, hardware).

## Features
- Logs play state: Direct Play / Direct Stream / Transcoding (video/audio)
- Captures title, user, device, resolution, codec, bitrate, and reason for transcode
- CSV log output for trend analysis
- Works on Windows, macOS, Linux; schedule with Task Scheduler or cron

## Quick Start
### 1) Requirements
- Python 3.9+
- `requests` package

```bash
pip install -r requirements.txt
