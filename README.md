# MultiMPDTool
Automatically downloads DRM L3 Content, decrypts it and combines Video and Audio.

# mpdl
An easier to understand and GUI-based version of this can be found here: [mpdl](https://github.com/DevLARLEY/mpdl)

# PSSHBoxTool
A tool for understading the PSSH can be found here: [PSSHBoxTool](https://github.com/DevLARLEY/PSSHBoxTool)

# Requirements
+ Python 3 (Tested on 3.12.0)
+ mp4decrypt (bento4)
+ ffmpeg
+ WKS-KEYS (with working CDM)

# Usage
+ Install python modules: `pip3 install -r requirements.txt`
+ Put all the requirements in the WKS-KEYS folder (with a working CDM in `pywidevine/L3/cdm/devices/android_generic`) and run MultiMPDTool: `python3 multimpdtool.py`

# Preview
![MultiMPDTool Showcase](https://i.imgur.com/OuUtNUg.png)
