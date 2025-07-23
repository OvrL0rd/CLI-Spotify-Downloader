## CLI-Spotify-Downloader
This script searches for (using spotify API) and downloads songs (using spotDL) to a folder structure like so:

    Root Folder (Folder Specified to download to):
    L Artist Name
      L Album Title
        L Artist - SongName.mp3

### Spotify API
This script relies on Spotify API tokens. There are two credentials that are needed from the user before the script can run.

    1. Client ID
    2. Client Secret

The script will prompt on first run to input these and you can edit them at any time. The keys are stored in the **.env** file.

In order to obtain your spotify API key go to [Spotify's docs page](https://developer.spotify.com/documentation/web-api/tutorials/getting-started)

### Import file
The import file is in json. Below is the structure necessary to import songs.

**Note:** The script will run through all data in the "songs" array listed.
    
    {
    "download_path": "/path/to/your/download/folder",
    "songs": [
        {"song_name": "Song Name", "artist_name": "Artist Name"},
        {"song_name": "Song Name", "artist_name": "Artist Name"},
        {"song_name": "Song Name", "artist_name": "Artist Name"}
    ]
    }

### Installation
Installation is simple. Clone the repo in your desired directory and run the setup script.

    git clone "ENTER URL HERE"

#### Setup Script
The setup script creates a virtual enviornment and installs dependencies where you can run Spotify-DWN.

In order to run the setup script make it executable and run it using:

    1. chmod +x setup.sh
    2. ./setup.sh


#### Bash Alias
In order to call the script for ease of access add an alias to your .bashrc to call the script if you desire. Or just run the script in your venv.

    alias activate_spotify-DWN_venv='source /path/to/venv/bin/activate'
    alias run_myscript='activate_spotify-DWN_venv && python /path/to/script.py'
