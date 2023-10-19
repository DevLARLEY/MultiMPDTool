# MultiMPDTool
Automatically downloads DRM L3 Content, decrypts it and combines Video and Audio.

# Disclaimer
It's not perfect yet, i'm already working on a tool that dumps the exact information contained in a PSSH and let's you create your own from System ID and Key ID (KID).

# Requirements
+ Python 3 (Tested on 3.12.0)
+ mp4decrypt (bento4)
+ ffmpeg
+ WKS-KEYS (with working CDM)

# Usage
+ Install python modules: `pip3 install -r requirements.txt`
+ Put all the requirements in the WKS-KEYS folder (with a working CDM) and run MultiMPDTool: `python3 multimpdtool.py`

# Preview
![MultiMPDTool Showcase](https://i.imgur.com/OuUtNUg.png)
