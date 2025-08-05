# Name: web_server.py
# Quick Desc: Web server for Spotify DWN
# Author: w1l238
# Project Link: https://github.com/w1l238/CLI-Spotify-Downloader 
# Desc:
#   Backend web server for Spotify Downloader
#   Program is able to:
#    - Search a song
#    - Display results
#    - Download a song
#    - Import a file to mass download songs
#    - Show live terminal results
#    - Edit API keys and path(s)

# Import statements
import eventlet
import eventlet.wsgi
from spotdl import Spotdl
from urllib.parse import quote_plus
from flask_socketio import SocketIO, emit
from flask import Flask, request, render_template, redirect, url_for, flash, get_flashed_messages, jsonify, session
from dotenv import load_dotenv
import requests
import subprocess
import os
import re
import sys
import json

# Flask app setup
app = Flask(__name__)

# Load key from .env
app.secret_key = os.getenv("FLASK_SECRET")

# Start the socketIO server to provide terminal output in webviewer
socketio = SocketIO(app)

#=================
# Helper Functions
#=================

# Get API token using Client ID and Client Secret
# If found return the access token
# If not found return 'None'
def generate_token(CLIENT_ID, CLIENT_SECRET):
    auth_response = requests.post('https://accounts.spotify.com/api/token', data={
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    })
    try:
        access_token = auth_response.json()['access_token']
        return access_token
    except:
        return None


# Searches spotify song after taking name and artist as input with spotify API access token generated from generate token function
# If song is found return the track artist, album name, track name, and track url
# If song not found return 'None'
def search_spotify_song(access_token, song_name, artist_name, limit):
    # Pass access token for auth using spotify API
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    # Query the search
    query = f"track:{song_name} artist:{artist_name}"
    # Filter the search to a track
    params = {
        "q": query,
        "type": "track",
        "limit": limit
    }
    # Spotify API endpoint
    search_url = "https://api.spotify.com/v1/search"

    # Store the response from API
    response = requests.get(search_url, headers=headers, params=params)
    
    # If the response fails return 'None'
    if response.status_code != 200:
        print(f"Spotify API search failed: {response.status_code} {response.text}")
        return []

    # Store results in json
    results = response.json()
    
    # Grab the needed data from the json
    tracks = results.get("tracks", {}).get("items", [])
    
    # If the needed data isn't found in the json from the API return 'None'
    if not tracks:
        print(f"No matching tracks found for '{song_name}' by '{artist_name}'.")
        return []

    # Store each part of the json in different variables
    # Track Name
    # Track Artist
    # Album Name
    # Track URL (Spotify's URL)
    # 
    track_list = [] # Dictionary of metadata for each track
    for track in tracks:
        images = track["album"].get("images", [])
        albumn_artwork_url = images[0]["url"] if images else None
        track_info = {
            "song": track["name"],
            "artist": ", ".join(artist["name"] for artist in track["artists"]),
            "album": track["album"]["name"],
            "url": track["external_urls"]["spotify"],
            "artwork": albumn_artwork_url
        }
        track_list.append(track_info) # Append to dictionary array
    # Print that the song was found
    print(f"Found {len(track_list)} tracks for '{song_name}' by '{artist_name}'.")

    # Return the data
    return track_list

# Set the destination path using the path the user requests
# Return the newly made folder or return the already valid folder
def set_folder(givn_folder):
    
    # If folder doesn't exist. Make it and return the path
    if not os.path.exists(givn_folder): 
        os.makedirs(givn_folder)
        print(f"\nCreating folder '{givn_folder}'...")
        return givn_folder
    
    # If the folder already exists then return it
    else:
        return givn_folder


# Create song folder structure function given song, album, and artist
def create_song_folder_structure(dest_path, artist, playlist, song_name):

    # Remove any spaces or illegal characters the playlists/artists used
    safe_artist = sanitize_filename(artist)
    safe_playlist = sanitize_filename(playlist)

    # Create the folder structure using the legal characters 
    artist_folder = os.path.join(dest_path, safe_artist)
    playlist_folder = os.path.join(artist_folder, safe_playlist)
    os.makedirs(playlist_folder, exist_ok=True)
    
    # Return the path to the playlist folder
    return playlist_folder


# Removes illegal characters to create a valid path for the OS
# Returns the legal path that the OS can use
def sanitize_filename(name):
    
    # Remove illegal characters for file/folder names
    return re.sub(r'[<>:"/\\|?*\n\r\t]', "_", name).strip()

# Download a specific song given the song's Spotify URL and the output path
# If song is found then download it using spotdl
# Falls back to yt-dlp if spotdl is unable to download due to audio provider error
# Falls back to yt-dlp if spotdl is unable to download due to audio provider error
# If spotfl throws error then output that an error occured
def download_spotify_url(spotify_url, output_folder):
        
    # Returns the folder where this script is stored
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Split path into parts
    parts = current_dir.split(os.sep)

    # Find index of the target folder
    try:
        idx = parts.index('CLI-Spotify-Downloader')
        # Rebuild path up to and including target folder
        current_dir = os.sep.join(parts[:idx + 1])
    except ValueError:
        # 'CLI-Spotify-Downloader' not found, keep current_dir as is or handle error
        pass

    # Spotdl's command to download a song using Spotify's song url
    command = [sys.executable, "-u", "-m", "spotdl", spotify_url]
    
    # Set the output folder for spotdl to use
    if output_folder:
        command.extend(["--output", output_folder])
    
    # Call spotdl to download the song
    try:
        # spotdl has it's own output here showing a progress bar and if it downloaded successfully etc.
        # Using popen to capture stdout to pass to front end web viewer
        spotdl_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

        all_output = ""

        # Output stdout to terminal and variable
        try:
            # read and show the command's stdout in real time
            for line in spotdl_process.stdout:
                # emit it back to the client (front end)
                print(line, end='')
                socketio.emit('stdout', {'data': line})
                socketio.sleep(0)
                all_output += line
                

            # Close the stream
            spotdl_process.stdout.close()

            # Get the return code
            return_code = spotdl_process.wait()

            # # If Spotdl encounters a audioprovider error then download using yt-dlp using yt URL
            # if "AudioProviderError" in all_output:
            yt_URL = re.search(r"AudioProviderError:.*-\s*(https?://\S+)", all_output) # Extract the URL

            if yt_URL:
                fallback_url = yt_URL.group(1)
                print(f"\nUsing fallback URL: {fallback_url}")

                # Local FFmpeg path in VENV (as spotdl doesn't place it correctly)
                print("[OS] Scanning Device Operating System...")
                if os.name == 'nt': # Windows
                    print("[OS] Device running Windows.")
                    ffmpeg_path = os.path.join(current_dir, 'venv', 'Scripts', 'ffmpeg.exe')
                elif os.name != 'nt': # Default to linux if not windows
                    print("[OS] Device running UNIX")
                    ffmpeg_path = os.path.join(current_dir, 'venv', 'bin', 'ffmpeg')

                # Check if ffmpeg path is valid
                if os.path.isfile(ffmpeg_path) or os.access(ffmpeg_path, os.X_OK):
                    # Download using yt-dlp and convert to mp3 using ffmpeg
                    yt_dlp_command = ["yt-dlp", fallback_url, "-P", output_folder, "-x", "--audio-format", "mp3", "--ffmpeg-location", ffmpeg_path]
                else:
                    # Warn user that ffmpeg isn't found
                    print("[WARN] ffmpeg package not found. Continuing to download without ffmpeg...")
           
                    # Download using yt-dlp and attempt to convert to mp3 without ffmpeg 
                    yt_dlp_command = ["yt-dlp", fallback_url, "-P", output_folder, "-x", "--audio-format", "mp3"]
                    
                # Call yt-dlp and stream the output to the wbe viewer
                yt_process = subprocess.Popen(yt_dlp_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

                # read and show the command's stdout in real time
                for line in yt_process.stdout:
                    # emit it back to the client (front end)
                    print(line, end='')
                    socketio.emit('stdout', {'data': line})
                    socketio.sleep(0)

                # Close the stream
                yt_process.stdout.close()
            
                # Get the return code
                return_code = yt_process.wait()
            # Get the return code
            return_code = spotdl_process.wait()

            # # If Spotdl encounters a audioprovider error then download using yt-dlp using yt URL
            # if "AudioProviderError" in all_output:
            yt_URL = re.search(r"AudioProviderError:.*-\s*(https?://\S+)", all_output) # Extract the URL

            if yt_URL:
                fallback_url = yt_URL.group(1)
                print(f"\nUsing fallback URL: {fallback_url}")

                # Download using yt-dlp and convert to mp3 using ffmpeg
                yt_dlp_command = ["yt-dlp", fallback_url, "-P", output_folder, "-x", "--audio-format", "mp3", "--ffmpeg-location", ffmpeg_path]
                    
                # Call yt-dlp and stream the output to the wbe viewer
                yt_process = subprocess.Popen(yt_dlp_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

                # read and show the command's stdout in real time
                for line in yt_process.stdout:
                    # emit it back to the client (front end)
                    print(line, end='')
                    socketio.emit('stdout', {'data': line})
                    socketio.sleep(0)

                # Close the stream
                yt_process.stdout.close()
            
                # Get the return code
                return_code = yt_process.wait()
        
            # If the call fails show that to the front end
            if return_code != 0:
                # emit a error message to web viewer client
                socketio.emit('stdout', {'data': f"Download failed with code {return_code}."})
            else:
                socketio.emit('download_complete', {'message': 'Download completed successfully!'})

        except Exception as e:
            socketio.emit('download_error', {'message': f"Error during download: {e}"})

    # If the calling of the command throws an error print it
    except subprocess.CalledProcessError as e: 
        print(f"Error during download: {e}")
        flash("Error during download. Please try again.")

# Imports and parses json file given the file's path
# Returns download path and each song in the json file
def parse_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['download_path'], [(s['song_name'], s['artist_name']) for s in data['songs']]

#====================
# App Route Functions
#====================

# Backend logic for root page (index.html)
@app.route("/", methods=["GET", "POST"])
def index():
    
    # When user submits the form (AKA searching for a song)
    if request.method == "POST":

        # Load env variables
        load_dotenv(override=True)

        # Spotify API Client Credentials
        CLIENT_ID = os.getenv("CLIENT_ID")
        CLIENT_SECRET = os.getenv("CLIENT_SECRET")
        print(f"ID and Secret: {CLIENT_ID}, {CLIENT_SECRET}")

        # Store user input as variables
        song_name = request.form.get("song_Name")
        artist_name = request.form.get("artist_Name")
        

        # Try to search for the song
        try:
            # Generate the token
            token = generate_token(CLIENT_ID,CLIENT_SECRET)
                
            if not token:
                flash("Unable to acquire token. Please check API credentials.", "error")
                return render_template("index.html")

            # Search for the spotify song
            song_data = search_spotify_song(token, song_name, artist_name, 5) # USE ONE FOR TESTING. WILL DEFAULT TO 5
                

            if not song_data or len(song_data) == 0:
                flash("No songs found. Please try a different title or artist.", "error")
                return redirect(url_for('index'))

            valid_tracks = [track for track in song_data if track.get("url")]
            if not valid_tracks:
                flash("No valid song URLs found in results.", "error")
                return redirect(url_for('index'))
            
            # Return the data
            return render_template('results.html', tracks=valid_tracks, query=f"{song_name} by {artist_name}")
        
        # If the song is unable to be searched for then print error and loop back to main menu
        except Exception as e:
            # Optionally log exception e somewhere for debugging
            flash("Error: Please check your API keys and try again.", "error")
            print(f"Error Message Code: {e}")
            return redirect(url_for('index'))

        # Else throw error and tell user and return
        else:
            flash("Song not found. Please try a different title or artist.", "error")
            return redirect(url_for('index'))

    return render_template("index.html")

# Import page logic for import.html
@app.route('/import', methods=["GET", "POST"])
def import_page():
    
    # On form submission run this if block
    if request.method == "POST":
        print("GOT POST STARTING...")

        # Load env variables
        load_dotenv(override=True)

        # Spotify API Client Credentials
        CLIENT_ID = os.getenv("CLIENT_ID")
        CLIENT_SECRET = os.getenv("CLIENT_SECRET")
        print(f"ID and Secret: {CLIENT_ID}, {CLIENT_SECRET}")

        # Store path from user
        import_file_path = request.form.get("import_Path")
        print(import_file_path)

        try:
            path, songs = parse_json_file(import_file_path)
            print(songs)
        
        except FileNotFoundError:
            flash(f"\nUnable to find import file with path '{import_file_path}' provided.")
            songs = []  # To avoid reference error
        
        except Exception as e:
            flash(f"Error found: '{e}'")
            songs = []

        song_data_list = [] # List to send to JS

        for song_name, artist_name in songs:
            # Generate token for Spotify's API
            token = generate_token(CLIENT_ID, CLIENT_SECRET)

            if token is None:
                flash("Unable to acquire token. Check your API keys.")
                return render_template("import_page.html")

            try:
                song_data = search_spotify_song(token, song_name, artist_name, 1)
                if not song_data:
                    flash(f"No data found for {song_name} by {artist_name}.")
                    continue

                track = song_data[0]

                if "url" in track and track["url"]:
                    # Define artist, album, song, url for folder creation and download
                    artist = track.get("artist")
                    album = track.get("album")
                    song = track.get("song")
                    url = track.get("url")

                    try:
                        dest_path = set_folder(path)
                    except OSError as e:
                        flash(f"Failed to create or access folder: {e}")
                        continue  # Skip this song on folder error

                    song_path = create_song_folder_structure(dest_path, artist, album, song)

                    #socketio.start_background_task(download_spotify_url, url, song_path)

                    # List of data to return
                    song_info = {
                        'track_url': url,
                        'download_path': song_path,
                        'song': song,
                        'album': album,
                        'artist': artist
                    }

                else:
                    flash(f"URL missing for track {track.get('song', 'unknown')} by {track.get('artist', 'unknown')}.")

            except Exception as e:
                flash(f"An error occurred: {e}")
                continue  # Continue looping over remaining songs

            # Append the song info
            if song_info:
                song_data_list.append(song_info)
                session['song_data_list'] = song_data_list
                print(f"Appending songs:\n {song_data_list}")

        print("Sending songs_data_list to front-end")
        return render_template("import_page.html")

    return render_template("import_page.html")


# Search results page logic (results.html)
@app.route('/results', methods=["GET", "POST"])
def results():
    
    # Store the download path from the user here
    #download_path = request.form.get("download_Path")

    

    # If the user selects to download a song
    if request.method == "POST":
        
        track_url = request.form.get("track_url")
        song = request.form.get("song")
        album = request.form.get("album")
        artist = request.form.get("artist")

        # Grab download path from .env
        DWN_PATH = os.getenv("DWN_PATH")

        # Make path if not already there
        os.makedirs(DWN_PATH, exist_ok=True)

        try:
            dest_path = set_folder(DWN_PATH)
        except OSError as e:
            flash(f"Failed to create or access folder: {e}")

        song_path = create_song_folder_structure(dest_path, artist, album, song)

        if not track_url:
            # Tell user that the URL can't be found
            flash("Download URL can't be found/isn't provided", "error")
            return render_template("results.html")
        
        # List of data to return
        song_info = {
            'track_url': track_url,
            'download_path': song_path,
            'song': song,
            'album': album,
            'artist': artist
        }

        session['song_info'] = song_info

        return redirect(url_for('download_page'))

# Download backend logic (download.html)
@app.route('/download', methods=["GET", "POST"])
def download_page():
    song_info = session.get('song_info', [])
    track_url = song_info.get("track_url")
    if not track_url:
        # Flash error if no URL is provided
        flash("No track URL provided to download", "error")
        return render_template("download.html")
    
    return render_template('download.html', track_url=track_url)

# Settings backend logic (settings.html)
@app.route('/settings', methods=["GET", "POST"])
def settings_page():

    # Load env variables
    load_dotenv(override=True)

    # Spotify API Client Credentials
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    DWN_PATH = os.getenv("DWN_PATH")
    print(f"ID and Secret: {CLIENT_ID}, {CLIENT_SECRET}, Download Path: {DWN_PATH}")

    # When user hits save button
    if request.method == "POST":
        # Store input as temp variables
        form_id = request.form.get("client-id")
        form_secret = request.form.get("client-secret")
        form_dwn = request.form.get("dwn_path")

        print(f"Form's ID: {form_id}")
        print(f"Form Secret: {form_secret}")
        print(f"Form Dwn Path: {form_dwn}")

        # Check if form data differs from current env values
        updated = False
        new_values = {}

        if form_id and form_id != CLIENT_ID:
            new_values["CLIENT_ID"] = form_id
            updated = True
        if form_secret and form_secret != CLIENT_SECRET:
            new_values["CLIENT_SECRET"] = form_secret
            updated = True
        if form_dwn and form_dwn != DWN_PATH:
            new_values["DWN_PATH"] = form_dwn
            updated = True

        if updated:
            # Read existing lines from .env
            env_path = ".env"
            lines = []
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    lines = f.readlines()
            
            # Update lines with new values or add them
            for key, val in new_values.items():
                found = False
                for i, line in enumerate(lines):
                    if line.strip().startswith(f"{key}="):
                        lines[i] = f'{key}="{val}"\n'
                        found = True
                        break
                if not found:
                    lines.append(f'{key}="{val}"\n')
            
            # Write back updated .env
            with open(env_path, "w") as f:
                f.writelines(lines)

            # Reload the environment variables after updating .env
            load_dotenv(override=True)

            # Optionally flash a message or redirect after saving
            flash("Saved Successfully.", "message")

        # Update current values for rendering after possible save
        CLIENT_ID = form_id
        CLIENT_SECRET = form_secret
        DWN_PATH = form_dwn

    # Render template, passing current values to pre-fill inputs
    return render_template(
        'settings.html',
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        dwn_path=DWN_PATH
    )


#=================
# Socket IO routes
# ================

# Start download (passed from js in 'download.html')
@socketio.on('start_download')
def handle_start_download(data):
    
    # Grab track url passed in
    track_url = data.get("track_url")

    # If url found then proceed to download
    if track_url:

        # Grab data passed in
        song = data.get("song")
        artist = data.get("artist")
        album = data.get("album")
        download_path = data.get("download_path")
        
        # Print artist, album, and song
        print(f"Artist: {artist}, Album: {album}, Song: {song}")

        # Start download using socketio
        socketio.start_background_task(download_spotify_url, track_url, download_path)
        
        # Emit download task started
        flash("Download task started, please wait...", "message")
    else:
        # Emit download error no URL provided
        flash("No track URL provided to start download", "error")

# Start loop download (called inside a for loop in import.html's JS)
@socketio.on('start_loop_download')
def handle_loop_download(data):

    # Grab track url passed in
    track_url = data.get("track_url")

    # Grab download path passed in
    download_path = data.get("download_path")

    # print(f"Track URL passed in and Download_path is: {track_url} && {download_path}")
    socketio.start_background_task(download_spotify_url, track_url, download_path)


# ==========
# API Routes
# ==========

# API to jsonify all songs that querys from 'import.html'
@app.route('/api/songs')
def get_songs_api():
    songs = session.get('song_data_list', [])
    return jsonify(songs)

# API to jsonify one song that querys from 'download.html' (which is the song selected from 'results.html')
@app.route('/api/song_info')
def get_song_info():
    song_info = session.get('song_info')
    if song_info is None:
        return jsonify({'error': 'No song info found'}), 404
    else:
        return jsonify(song_info)

# API to clear backend session (to prevent page reload on 'download.html/import.html'to rerun command)
@app.route('/api/clear-songs', methods=['POST'])
def clear_songs():
    print("Clearing import session...")
    session.pop('song_data_list', None)
    return '', 204


if __name__ == "__main__":
    socketio.run(app, debug=True)
