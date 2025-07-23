## CLI-Spotify-Downloader
This script searches for (using Spotify's API) and downloads songs (using SpotDL) to a folder structure like so:

    Root Folder (Folder specified to download to):
    L Artist Name
      L Album Title
        L Artist - SongName.mp3

### Spotify API
This script relies on Spotify API tokens. There are two credentials that are needed from the user before the script can run.

    a. Client ID
    b. Client Secret

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

    1. git clone https://github.com/w1l238/CLI-Spotify-Downloader
    2. cd CLI-Spotify-Downloader

#### Setup Script
The setup script creates a virtual enviornment and installs dependencies where you can run Spotify-DWN.

In order to run the setup script make it executable and run it using:

    3. chmod +x setup.sh
    4. ./setup.sh

Once the setup script has successfully installed the dependencies. Use the following command to activate the venv to run the script.

    5. source venv/bin/activate
    6. python3 CLI-Spotify-DWN.py

#### Credit
Spotdl can be found [here](https://github.com/spotDL/spotify-downloader)
