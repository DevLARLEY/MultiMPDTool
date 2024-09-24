import datetime
import glob
import os
import uuid
from os.path import exists
from subprocess import Popen, PIPE

import ffmpeg
import json
import requests
import xmltodict
import yt_dlp
import yt_dlp.options
from pywidevine import Cdm, PSSH, Device


class color:
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class style:
    INFO = '[' + color.GREEN + 'INFO' + color.END + '] '
    WARN = '[' + color.YELLOW + 'WARN' + color.END + '] '
    ERROR = '[' + color.RED + 'EROR' + color.END + '] '


def format_seconds(
        seconds: int
) -> str:
    m, seconds = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f'{int(h)}h {int(m)}m {int(seconds)}s'


def getPSSH(
        mpd_url: str
) -> str | None:
    pssh = None
    try:
        r = requests.get(url=mpd_url)
        r.raise_for_status()
        xml = xmltodict.parse(r.text)
        mpd = json.loads(json.dumps(xml))
        periods = mpd['MPD']['Period']
    except Exception:
        return
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
        return
    return pssh


def queryForMedia():
    print(style.INFO + 'Input Encrypted Video/Audio Files:')
    video, audio = input(style.INFO + '+ Encrypted Video File: '), input(style.INFO + '+ Encrypted Audio File: ')
    if not video and not audio:
        print(style.ERROR + "No input files provided.")
        exit(-1)
    return video, audio


def queryForHeaders():
    headers = open("headers.py", "w")
    print(style.INFO + 'Input headers/params in Python requests format (type ";;" to END):')
    cont = False
    for line in iter(input, ';;'):
        if 'headers' in line.lower():
            cont = True
        headers.write(str(line) + "\n")
    if not cont:
        headers.write("headers = {}" + "\n")
    headers.close()


def chooseHeaders():
    s = input(style.INFO + 'Input headers (y/n)? ~: ')
    if s.lower() == 'y':
        return True
    else:
        return False


def queryForKeys():
    keys = []
    print(style.INFO + 'Input Decryption Key(s):')
    while True:
        i = input('')
        if not i:
            break
        keys.append(i)
    return keys


def queryForMPD():
    mpd = input(style.INFO + 'Input .mpd URL ~: ')
    if not mpd:
        print(style.ERROR + 'No .mpd URL provided.')
        exit(-1)
    return mpd


def clearHeaders():
    with open("headers.py", "w") as f:
        f.write("headers = {}")


def printLogo():
    print()
    print(color.CYAN + "       ___ ___      ____     " + color.PURPLE + "___  __ _____ ______" + color.BLUE + " _______         __")
    print(color.CYAN + "      /__//__/|    /_/_/|   " + color.PURPLE + "/__/ /_//____//_____/" + color.BLUE + "/______/|       /_/|")
    print(color.CYAN + "      |  \\/  ||_  _| | ||(_)" + color.PURPLE + "|  \\/  |  __ \\|  __ \\" + color.BLUE + "__   __|/_  ____| ||")
    print(color.CYAN + "      | \\  / |L/ /_| | |L/_/" + color.PURPLE + "| \\  / | |/_) | || | ||" + color.BLUE + "| ||___/\\/___/| ||")
    print(color.CYAN + "      | |\\/| | |_| | | __| |" + color.PURPLE + "| |\\/| |  ___/| ||_| ||" + color.BLUE + "| |/ _ \\// _ \\| ||")
    print(color.CYAN + "      | || | | |_| | | |_| |" + color.PURPLE + "| || | | ||   | |/_| ||" + color.BLUE + "| | (_) | (_) | ||")
    print(color.CYAN + "      |_|/ |_|\\__,_|_|\\__|_|" + color.PURPLE + "|_|/ |_|_|/   |_____// " + color.BLUE + "|_|\\___/ \\___/|_|/" + color.END)
    print("                     (c) https://github.com/DevLARLEY")
    print()


def getKeys(
        pssh,
        lic_url
) -> list | None:
    files = glob.glob('CDM/*.wvd')

    device = Device.load(files[0])
    cdm = Cdm.from_device(device)
    session_id = cdm.open()

    challenge = cdm.get_license_challenge(session_id, PSSH(pssh))

    response = requests.post(
        url=lic_url,
        data=challenge
    )

    if 200 > response.status_code > 299:
        print(f"Unable to obtain decryption keys, got error code {response.status_code}: \n{response.text}")
        print("License wrapping may be in use.")
        return

    try:
        cdm.parse_license(session_id, response.content)
    except Exception:
        print(f"Unable to obtain decryption keys: \n{response.text}")
        print("License wrapping may be in use.")
        return

    keys = list(
        map(
            lambda key: f"{key.kid.hex}:{key.key.hex()}",
            filter(
                lambda key: key.type == 'CONTENT',
                cdm.get_keys(session_id)
            )
        )
    )
    cdm.close(session_id)
    return keys if keys else None


class Main:
    def __init__(self):
        self.video_file = None
        self.audio_file = None
        self.current_media_type = 'Video'

    def log(
            self,
            data: dict
    ):
        done = data.get('status') == 'finished'
        name = data.get('filename')

        size, progress = 0, 0
        if (
                (size_estimate := data.get('total_bytes_estimate')) and
                (size_downloaded := data.get('downloaded_bytes'))
        ):
            if size_estimate:
                size = int(size_estimate / 1000000)
                if size_downloaded:
                    progress = int(size_downloaded / size_estimate * 100)

        eta = 'N/A'
        if eta_data := data.get('eta'):
            eta = format_seconds(eta_data)

        frags = f"{data.get('fragment_index', '?')}/{data.get('fragment_count', '?')}"

        if speed := data.get('speed', 0):
            speed = int(speed / 1000)

        if progress <= 25:
            percent = f'{color.RED}{round(progress) + 1}%{color.END}'
        elif 25 < progress <= 75:
            percent = f'{color.YELLOW}{round(progress) + 1}%{color.END}'
        elif progress > 75:
            percent = f'{color.GREEN}{round(progress) + 1}%{color.END}'
        else:
            percent = color.RED + '??.?%' + color.END

        progress_message = (
            f'{style.INFO}Progress ({self.current_media_type}): {percent} (ETA: {eta}, Frags: {frags}, {speed} KB/s, {size} MB)'
        )

        if name:
            if self.current_media_type == 'Video':
                self.video_file = name
            elif self.current_media_type == 'Audio':
                self.audio_file = name

        if done:
            print()
            if progress == 0:
                progress_message = ''
                self.current_media_type = 'Audio'

        print('\r' + progress_message, end="")

    # TODO
    #  + Add support for local .mpd files
    #  + If decrypting local files, give option to decrypt using PSSH and License URL

    def run(self):
        printLogo()

        reqs = ['mp4decrypt.exe']
        for r in reqs:
            if not exists(r):
                print(style.ERROR + 'Requirement not found in current directory: ' + r)
                exit(-1)

        mpd = None
        pssh = None
        source_option = int(input(style.INFO + 'Select Input Type => (1) .mpd File, (2) Video/Audio Files ~: '))

        if source_option == 1:
            mpd = queryForMPD()

            pssh = getPSSH(mpd)
            if pssh:
                print(style.INFO + "PSSH => " + str(pssh))
            else:
                pssh = input(style.ERROR + "No PSSH found. Enter manually ~: ")
                if pssh == '':
                    print(style.ERROR + "No PSSH was entered.")
                    exit(-1)

        elif source_option == 2:
            self.video_file, self.audio_file = queryForMedia()

        if source_option == 1:
            decryption_option = int(input(style.INFO + 'Select Decryption Type => (1) License URL, (2) Key(s) ~: '))

            if decryption_option == 1:
                lic = input(style.INFO + 'Input License URL: ')
                if chooseHeaders():
                    queryForHeaders()
                else:
                    clearHeaders()

                keys = getKeys(pssh, lic)
                if not keys:
                    print(style.ERROR + "Unable to extract key(s).")
                    exit(-1)

            elif decryption_option == 2:
                keys = queryForKeys()
                if not keys:
                    print(style.ERROR + 'No Keys provided.')
                    exit(-1)

            else:
                print(style.ERROR + 'No option was chosen.')
                exit(-1)

        elif source_option == 2:
            keys = queryForKeys()
            if not keys:
                print(style.ERROR + 'No Keys provided.')
                exit(-1)

        else:
            print(style.ERROR + 'No option was chosen.')
            exit(-1)

        process_id = str(uuid.uuid4())

        output = input(style.INFO + "Enter the output name without the file extension ~: ")

        if source_option == 1:
            print(style.INFO + 'Downloading .mpd file ...')
            ydl_opts = {
                'allow_unplayable_formats': True,
                'noprogress': True,
                'quiet': True,
                'fixup': 'never',
                'format': 'bv,ba',
                'no_warnings': True,
                'outtmpl': {'default': process_id + '.f%(format_id)s.%(ext)s'},
                'progress_hooks': [self.log]
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download(mpd)
            except Exception:
                print(style.ERROR + "Unable to download .mpd file.")
                exit(-1)
            print(style.INFO + "Download successful.")

        print(style.INFO + "Decrypting ...")
        for media in (self.video_file, self.audio_file):
            if not media:
                continue

            media_type = 'video' if media == self.video_file else 'audio'

            extension = os.path.splitext(media)[-1]
            output_file = f'{process_id}.{media_type}.{extension}'

            command = (
                'mp4decrypt.exe',
                *sum([['--key', i] for i in keys], []),
                media,
                output_file
            )

            process = Popen(command, stdout=PIPE, stderr=PIPE)
            _, stderr = process.communicate()

            if errors := stderr.decode('utf-8'):
                print(style.ERROR + "Failed decrypting " + media + ": " + errors)
                exit(-1)

            print(style.INFO + "Successfully decrypted " + media + '.')

            if media_type == 'video':
                self.video_file = output_file
            else:
                self.audio_file = output_file

            if os.path.exists(media):
                os.remove(media)

        t = datetime.datetime.now()

        if not output:
            output = (
                    process_id +
                    '.{}-{}-{}_{}-{}-{}'.format(t.day, t.month, t.year, t.hour, t.minute, t.second) +
                    '.mkv'
            )
        else:
            output += '.mkv'

        if self.video_file and self.audio_file:
            print(style.INFO + "Muxing ...")

            video = ffmpeg.input(self.video_file)
            audio = ffmpeg.input(self.audio_file)

            stream = ffmpeg.output(video, audio, output, vcodec='copy', acodec='copy')
            stream = ffmpeg.overwrite_output(stream)

            ffmpeg.run(stream, quiet=True)

            if os.path.exists(self.video_file):
                os.remove(self.video_file)
            if os.path.exists(self.audio_file):
                os.remove(self.audio_file)

        clearHeaders()
        print(style.INFO + "Output file => " + output)


if __name__ == '__main__':
    try:
        main = Main()
        main.run()
    except KeyboardInterrupt:
        exit(-1)
