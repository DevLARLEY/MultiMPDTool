from os.path import exists
from subprocess import Popen, PIPE
from pprint import pprint
import requests, xmltodict, json, urllib.request
import yt_dlp.options
import yt_dlp
import ffmpeg
import pathlib
import datetime
import math, uuid
import sys, os, re

typ = 'Video'
src = [None] * 2

def printLogo():
	print()
	print(col.CYAN + "       ___ ___      ____     " + col.PURPLE + "___  __ _____ ______" + col.BLUE + " _______         __")
	print(col.CYAN + "      /__//__/|    /_/_/|   " + col.PURPLE + "/__/ /_//____//_____/" + col.BLUE + "/______/|       /_/|")
	print(col.CYAN + "      |  \\/  ||_  _| | ||(_)" + col.PURPLE + "|  \\/  |  __ \\|  __ \\" + col.BLUE + "__   __|/_  ____| ||")
	print(col.CYAN + "      | \\  / |L/ /_| | |L/_|" + col.PURPLE + "| \\  / | |/_) | || | ||" + col.BLUE + "| ||___/|/___/| ||")
	print(col.CYAN + "      | |\\/| | |_| | | __| |" + col.PURPLE + "| |\\/| |  ___/| ||_| ||" + col.BLUE + "| |/ _ \\// _ \\| ||")
	print(col.CYAN + "      | || | | |_| | | |_| |" + col.PURPLE + "| || | | ||   | |/_| ||" + col.BLUE + "| | (_) | (_) | ||")
	print(col.CYAN + "      |_|/ |_|\\__,_|_|\\__|_|" + col.PURPLE + "|_|/ |_|_|/   |_____// " + col.BLUE + "|_|\\___/ \\___/|_|/" + col.ENDC)
	print("                     (c) https://github.com/DevLARLEY")
	print()

class col:
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class pref:
	INFO = '[' + col.GREEN + 'INFO' + col.ENDC + '] '
	WARN = '[' + col.YELLOW + 'WARN' + col.ENDC + '] '
	ERROR = '[' + col.RED + 'EROR' + col.ENDC + '] '

# Credit: WKS-KEYS
def getKeys(pssh, lic_url, cert_b64=None):
	import base64, sys
	try:
		import headers
	except Exception:
		print(pref.ERROR + "Unable to parse headers.")
		sys.exit()
	from pywidevine.L3.cdm import cdm, deviceconfig
	from base64 import b64encode
	from pywidevine.L3.getPSSH import get_pssh
	from pywidevine.L3.decrypt.wvdecryptcustom import WvDecrypt
	try:
		wvdecrypt = WvDecrypt(init_data_b64=pssh, cert_data_b64=cert_b64, device=deviceconfig.device_android_generic)            
		widevine_license = requests.post(url=lic_url, data=wvdecrypt.get_challenge(), headers=headers.headers)
		license_b64 = b64encode(widevine_license.content)
		wvdecrypt.update_license(license_b64)
		correct, keyswvdecrypt = wvdecrypt.start_process()
		return correct, keyswvdecrypt
	except Exception:
		print(pref.ERROR + "Unable to get Key(s).")
		sys.exit()

# Credit: https://github.com/medvm/widevine_keys/blob/main/getPSSH.py
def getPSSH(mpd_url):
    pssh = ''
    correct = True
    try:
        r = requests.get(url=mpd_url)
        r.raise_for_status()
        xml = xmltodict.parse(r.text)
        mpd = json.loads(json.dumps(xml))
        periods = mpd['MPD']['Period']
    except Exception as e:
        correct = False
    try: 
        if isinstance(periods, list):
            for idx, period in enumerate(periods):
                if isinstance(period['AdaptationSet'], list):
                    for ad_set in period['AdaptationSet']:
                        if ad_set['@mimeType'] == 'video/mp4':
                            try:
                                for t in ad_set['ContentProtection']:
                                    if t['@schemeIdUri'].lower() == "urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed":
                                        pssh = t["cenc:pssh"]
                            except Exception:
                                pass   
                else:
                    if period['AdaptationSet']['@mimeType'] == 'video/mp4':
                            try:
                                for t in period['AdaptationSet']['ContentProtection']:
                                    if t['@schemeIdUri'].lower() == "urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed":
                                        pssh = t["cenc:pssh"]
                            except Exception:
                                pass   
        else:
            for ad_set in periods['AdaptationSet']:
                    if ad_set['@mimeType'] == 'video/mp4':
                        try:
                            for t in ad_set['ContentProtection']:
                                if t['@schemeIdUri'].lower() == "urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed":
                                    pssh = t["cenc:pssh"]
                        except Exception:
                            pass   
    except Exception:
        correct = False                   
    return correct, pssh

def getPSSH2(mpd_url):
	pssh = []
	try:
		name, headers = urllib.request.urlretrieve(mpd_url)
	except Exception:
		print(pref.ERROR + "Bad URL.")
		sys.exit()
	f = open(name, "r").read()
	res = re.findall('<cenc:pssh.*>.*<.*/cenc:pssh>', f)
	for r in res:
		try:
			r = r.split('>')[1].split('<')[0]
			pssh.append(r)
		except Exception:
			pass
	if pssh:
		return min(pssh, key=len)
	else:
		return ''

def chooseSource():
	s = input(pref.INFO + 'Select Input Type => (1) .mpd File, (2) Video/Audio Files ~: ')
	if s != '1' and s != '2':
		print(pref.ERROR + 'No option was chosen.')
		sys.exit()
	else:
		return int(s)

def queryForMedia():
	media = [None] * 2
	print(pref.INFO + 'Input Encrypted Video/Audio Files:')
	vid = input(pref.INFO + '+ Encrypted Video File: ')
	media[0] = vid
	aud = input(pref.INFO + '+ Encrypted Audio File: ')
	media[1] = aud
	if not vid and not aud:
		print(pref.ERROR + "No input files provided.")
		sys.exit()
	return media

def chooseDecryption():
	s = input(pref.INFO + 'Select Decryption Type => (1) License URL, (2) Key(s) ~: ')
	if s != '1' and s != '2':
		print(pref.ERROR + 'No option was chosen.')
		sys.exit()
	else:
		return int(s)

def queryForHeaders():
	headers = open("headers.py", "w")
	print(pref.INFO + 'Input headers/params in Python requests format (type ";;" to END):')
	cont = False
	for line in iter(input, ';;'):
		if 'headers' in line.lower():
			cont = True
		headers.write(str(line) + "\n")
	if not cont:
		headers.write("headers = {}" + "\n")
	headers.close()

def chooseHeaders():
	s = input(pref.INFO + 'Input headers (y/n)? ~: ')
	if s.lower() == 'y':
		return True
	else:
		return False

def queryForKeys():
	keys = ''
	print(pref.INFO + 'Input Decryption Key(s):')
	while True:
		i = input('')
		if not i:
			break
		keys += (' --key ' + str(i))
	return keys

def queryForLicense():
	return input(pref.INFO + 'Input License URL: ')

def queryForMPD():
	mpd = input(pref.INFO + 'Input .mpd URL ~: ')
	if not mpd:
		print(pref.ERROR + 'No .mpd URL provided.')
		sys.exit()
	return mpd

def clearHeaders():
	headers = open("headers.py", "w")
	headers.write("headers = {}")
	headers.close()

def log(d):

	done = False
	if 'status' in d:
		statusT = d['status']
		if statusT is not None:
			if statusT == 'finished':
				done = True

	name = None
	if 'filename' in d:
		nameT = d['filename']
		if nameT is not None:
			name = nameT

	perc = 0
	if 'total_bytes_estimate' in d and 'downloaded_bytes' in d:
		tbeT, tbT = d['total_bytes_estimate'], d['downloaded_bytes']
		if tbeT is not None and tbT is not None:
			perc = tbT/tbeT*100

	size = 0
	if 'total_bytes_estimate' in d:
		tbeT = d['total_bytes_estimate']
		if tbeT is not None:
			size = tbeT/1000000

	eta = 'N/A'
	if 'eta' in d:
		etaT = d['eta']
		if etaT is not None:
			m, s = divmod(etaT, 60)
			h, m = divmod(m, 60)
			eta = ('{}:{}:{}'.format(int(h), int(m), int(s)))

	frags = '?/?'
	if 'fragment_count' in d and 'fragment_index' in d:
		fcT, fiT = d['fragment_count'], d['fragment_index']
		if fcT is not None and fiT is not None:
			frags = (str(fiT) + '/' + str(fcT))

	speed = '0.0'
	if 'speed' in d:
		sT = d['speed']
		if sT is not None:
			speed = str(int(sT/1000))

	if int(perc) <= 25:
		percent = col.RED + str(math.ceil(perc)) + '%' + col.ENDC
	if int(perc) > 25:
		percent = col.YELLOW + str(math.ceil(perc)) + '%' + col.ENDC
	if int(perc) > 75:
		percent = col.GREEN + str(math.ceil(perc)) + '%' + col.ENDC

	global typ
	stat = pref.INFO + 'Progress (' + typ + '): ' + percent + ' (ETA: ' + eta + ', Frags: ' + frags + ', ' + speed + ' KB/s, ' + str(int(size)) + ' MB)'

	global src
	if name is not None:
		if typ == 'Video':
			src[0] = name
		elif typ == 'Audio':
			src[1] = name

	l = (os.get_terminal_size().columns-len(stat))	
	if l > 0:
		stat += ' ' * l
	
	if done:
		print("")
	if perc == 0:
		stat = ''
		typ = 'Audio'
	print("\r" + stat, end="")

# TODO
#  + Add support for local .mpd files
#  + If decrypting local files, give option to decrypt using PSSH and License URL

def main():
	printLogo()

	global typ
	typ = 'Video'

	#Check for requirements
	reqs = ['mp4decrypt.exe']
	for r in reqs:
		if not exists(r):
			print(pref.ERROR + 'Requirement not found in current directory: ' + r)
			sys.exit()

	#Select Input
	global src
	mpd = None
	pssh = None
	ch = chooseSource()
	if ch == 1:
		mpd = queryForMPD()
		correct, pssh = getPSSH(mpd)
		if correct and pssh != '':
			print(pref.INFO + "PSSH => " + str(pssh))
		else:
			pssh = getPSSH2(mpd)
			if pssh != '':
				print(pref.INFO + "PSSH => " + str(pssh))
			else:
				pssh = input(pref.ERROR + "No PSSH found. Enter manually ~: ")
				if pssh == '':
					print(p.ERROR + "No PSSH was entered.")
					sys.exit()
		 # TODO also check here if PSSH is valid
	elif ch == 2:
		src = queryForMedia()
	
	#Select Decryption
	if ch == 1:
		ch2 = chooseDecryption()
		if ch2 == 1:
			lic = queryForLicense()
			if chooseHeaders():
				queryForHeaders()
			else:
				clearHeaders()
			keys = ''
			correct, keyz = getKeys(pssh, lic)
			if correct and keyz:
				for k in keyz:
					keys += ' --key ' + k
			else:
				print(pref.ERROR + "Unable to extract key(s).")
				sys.exit()
		elif ch2 == 2:
			#Input Keys
			keys = queryForKeys()
			if keys == '':
				print(pref.ERROR + 'No Keys provided.')
				sys.exit()
	elif ch == 2:
		#Input Keys
		keys = queryForKeys()
		if keys == '':
			print(pref.ERROR + 'No Keys provided.')
			sys.exit()

	ident = str(uuid.uuid4())	

	#Download mpd file
	if ch == 1:
		print(pref.INFO + 'Downloading .mpd file ...')
		ydl_opts = {
		'allow_unplayable_formats': True,
		'noprogress': True,
		'quiet': True,
 		'fixup': 'never',
 		'format': 'bv,ba',
 		'no_warnings': True,
 		'outtmpl': {'default': ident + '.f%(format_id)s.%(ext)s'},
 		'progress_hooks': [log]
 		}
		try:
			with yt_dlp.YoutubeDL(ydl_opts) as ydl:
				ydl.download(mpd)
		except Exception:
			print(pref.ERROR + "Unable to download .mpd file.")
			sys.exit()
		print(pref.INFO + "Download successful.")

	#Decrypt video and audio
	print(pref.INFO + "Decrypting ...")
	for s in src:
		i = src.index(s)
		t = None
		if i == 0:
			t = 'video'
		elif i == 1:
			t = 'audio'	
		su = pathlib.Path(s).suffix
		out = (ident + "." + t + su)
		if s != '':
			process = Popen("mp4decrypt.exe " + keys + ' ' + s + ' ' + out, stdout=PIPE, stderr=PIPE)
			stdout, stderr = process.communicate()
			if stderr.decode('utf-8'):
				print(pref.ERROR + "Failed decrypting " + s + ": " + stderr.decode('utf-8'))
				sys.exit()
			print(pref.INFO + "Successfully decrypted " + t + '.')
			src[i] = out
			if os.path.exists(s):
				os.remove(s)
		else:
			print(pref.WARN + "Skipped " + t + ".")

	#Combine files if 2 present
	src = [r.replace('"', '') for r in src]
	t = datetime.datetime.now()
	out = (ident + '.{}-{}-{}_{}-{}-{}'.format(t.day, t.month, t.year, t.hour, t.minute, t.second) + '.mp4')
	if len(src) == 2:
		print(pref.INFO + "Combining files ...")
		v = ffmpeg.input(src[0])
		a = ffmpeg.input(src[1])
		stream = ffmpeg.output(v, a, out, vcodec='copy', acodec='copy')
		stream = ffmpeg.overwrite_output(stream)
		ffmpeg.run(stream, quiet=True)
		if os.path.exists(src[0]):
			os.remove(src[0])
		if os.path.exists(src[1]):
			os.remove(src[1])

	clearHeaders()
	print(pref.INFO + "Output file => " + out)

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		sys.exit()
