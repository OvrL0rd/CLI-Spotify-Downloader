# Dev Branch
This is the dev branch for CLI-Spotify-Downloader. Current changes that are in place for this branch include:

- [x] yt-dlp fallback
- [x] Web Server (Work in progress...)
- [x] Updated install scripts for linux
- [ ] Add windows install script

## Issues
Currently (as of 8/5/25) SpotDL is unable to download songs.
YT-DLP is the fallback and requires ffmpeg to download songs correctly. Below are the steps to add ffmpeg:


### Used the setup script
If you ran the 'setup.sh' script ffmpeg is installed in the default path

Linux:
    ~/.spotdl/ffpmeg

Windows:
    C:\user\$USERNAME\.spotdl\ffpmeg.exe

Move the file and place into your venv

Path on Linux:

    venv/bin/

Path on Windows:

    venv/scripts/

### Didn't use script
If you didn't use the 'setup.sh' script you need to install ffmpeg using this command and move into the folder specified above

    spotdl --download-ffmpeg

# CLI-Spotify-Downloader
This python script downloads songs to your machine in a folder structure (shown below). This script is great for automating the download process but also the organization of songs, artists, and albums using the folder structure.

Folder Structure:

    Root Folder (Folder specified to download to)
    L Artist Name
      L Album Title
        L Artist - SongName.mp3

## Prerequisites
There are a few things you need to obtain prior to running this script. Below are the steps needed to run the script properly.

### Spotify API
This script relies on Spotify API tokens. There are two credentials that are needed from the user before the script can properly work.

- Client ID
- Client Secret

The script will prompt to input these if you haven't already and you can edit them within the script. The keys are stored in the **.env** file if you need access to it.

In order to obtain your spotify API key go to [Spotify's docs](https://developer.spotify.com/documentation/web-api/tutorials/getting-started)

### Import file
The script also has a file import option. This option can allow you to mass download songs to a specified folder. The script will run through all data in the "songs" array listed. Below is the structure necessary to import songs. 

**Note:** It is recommended to put your full folder path here. Do not use alias like '~' or '$HOME' here as it will place it in the script path instead.
    
    {
      "download_path": "/path/to/your/download/folder",
      "songs": [
        {"song_name": "Song Name", "artist_name": "Artist Name"},
        {"song_name": "Song Name", "artist_name": "Artist Name"},
        {"song_name": "Song Name", "artist_name": "Artist Name"}
      ]
    }

### Installation
To install, clone the repo in your desired directory and run the setup script.

    git clone https://github.com/w1l238/CLI-Spotify-Downloader && cd CLI-Spotify-Downloader

#### Setup Script (linux only)
The setup script creates a virtual enviornment and installs dependencies where you can run Spotify-Downloader.

In order to run the setup script make it executable and run it using:

    chmod +x setup.sh
    ./setup.sh

Once the setup script has successfully installed the dependencies. Use the following command to activate the vritual environment to run the script.

    source venv/bin/activate
    python3 CLI-Spotify-DWN.py

#### Bare Metal Install
You can always download the dependencies on your machine instead (Bare metal install). The list of python dependencies are:
    
    requests
    python-dotenv
    spotdl

Within spotdl you might have to install ffmpeg use this command if needed:

    spotdl --download-ffmpeg

## Credit
- Spotdl can be found [here](https://github.com/spotDL/spotify-downloader)
