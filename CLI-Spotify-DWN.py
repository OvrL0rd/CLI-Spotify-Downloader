# Name: CLI-Spotify-DWN.py
# Quick Desc: Main driver file for CLI-Spotify-Downloader
# Author: w1l238
# Project Link: https://github.com/w1l238/CLI-Spotify-Downloader
# Desc:
#   This program will be able to...
#   - Search and Download Spotify Songs
#   - Specify folder to place songs into
#   - Make folder structure for each song as follows:
#       Song artist
#       L Song Playlist
#           L Song Name (Song Name - Artist Name.mp3)
#
#   - Mass download via json file importing
#   - Edit API keys

# Import
import os
import re
import requests
import subprocess
import sys
import time
import json
from dotenv import load_dotenv

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
def search_spotify_song(access_token, song_name, artist_name):
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
        "limit": 1
    }
    # Spotify API endpoint
    search_url = "https://api.spotify.com/v1/search"

    # Store the response from API
    response = requests.get(search_url, headers=headers, params=params)
    
    # If the response fails return 'None'
    if response.status_code != 200:
        print(f"Spotify API search failed: {response.status_code} {response.text}")
        return None, None, None, None

    # Store results in json
    results = response.json()
    
    # Grab the needed data from the json
    tracks = results.get("tracks", {}).get("items", [])
    
    # If the needed data isn't found in the json from the API return 'None'
    if not tracks:
        print(f"No matching tracks found for '{song_name}' by '{artist_name}'.")
        return None, None, None, None

    # Store each part of the json in different variables
    # Track Name
    # Track Artist
    # Album Name
    # Track URL (Spotify's URL)
    # 
    track = tracks[0] # Start at the beginning
    track_name = track["name"]
    track_artist = ", ".join(artist["name"] for artist in track["artists"])
    album_name = track["album"]["name"]
    track_url = track["external_urls"]["spotify"]

    # Print that the song was found
    print(f"'{track_name}' by {track_artist} on album '{album_name}' found.")

    # Return the data
    return track_artist, album_name, track_name, track_url


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


# Download a specific song given the song's Spotify URL and the output path
# If song is found then download it using spotdl
# Falls back to yt-dlp if spotdl is unable to download due to audio provider error
# If spotfl throws error then output that an error occured
def download_spotify_url(spotify_url, output_folder):
    
    # Returns the folder where this script is stored
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Local FFmpeg path in VENV (as spotdl doesn't place it correctly)
    if os.name == 'nt': # Windows
        ffmpeg_path = os.path.join(current_dir, 'venv', 'Scripts', 'ffmpeg.exe')
    elif os.name != 'nt': # Default to linux if not windows
        ffmpeg_path = os.path.join(current_dir, 'venv', 'bin', 'ffmpeg')

    # Spotdl's command to download a song using Spotify's song url
    command = [sys.executable, "-m", "spotdl", spotify_url]
    
    # Set the output folder for spotdl to use
    if output_folder:
        command.extend(["--output", output_folder])
    
    # Call spotdl to download the song
    try:
        # spotdl has it's own output here showing a progress bar and if it downloaded successfully etc.
        spotdl_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        all_output = ""

        # Output stdout to terminal and variable
        for line in spotdl_process.stdout:
            print(line, end='')
            all_output += line

        # If Spotdl encounters a audioprovider error then download using yt-dlp using yt URL
        if "AudioProviderError" in all_output:
            yt_URL = re.search(r"AudioProviderError:.*-\s*(https?://\S+)", all_output) # Extract the URL

            if yt_URL:
                fallback_url = yt_URL.group(1)
                print(f"\nUsing fallback URL: {fallback_url}")

                # Download using yt-dlp and convert to mp3 using ffmpeg
                yt_dlp_command = ["yt-dlp", fallback_url, "-P", output_folder, "-x", "--audio-format", "mp3", "--ffmpeg-location", ffmpeg_path]
                
                # Call yt-dlp
                subprocess.run(yt_dlp_command)

    # If the calling of the command throws an error print it
    except subprocess.CalledProcessError as e: 
        print(f"Error during download: {e}")

    except Exception as e:
        print(f"Subprocess error: {e}")

# Removes illegal characters to create a valid path for the OS
# Returns the legal path that the OS can use
def sanitize_filename(name):
    
    # Remove illegal characters for file/folder names
    return re.sub(r'[<>:"/\\|?*\n\r\t]', "_", name).strip()

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


# Display the search menu and takes the user's input
# Returns the song and artist name
def search_song():
    
    clear_screen()
    print("""
░██████╗███████╗░█████╗░██████╗░░█████╗░██╗░░██╗
██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██║░░██║
╚█████╗░█████╗░░███████║██████╔╝██║░░╚═╝███████║
░╚═══██╗██╔══╝░░██╔══██║██╔══██╗██║░░██╗██╔══██║
██████╔╝███████╗██║░░██║██║░░██║╚█████╔╝██║░░██║
╚═════╝░╚══════╝╚═╝░░╚═╝╚═╝░░╚═╝░╚════╝░╚═╝░░╚═╝\n""")
    
    song_name = input("  Song Name: ")
    artist_name = input("Artist Name: ")
    
    return song_name, artist_name

# Displays the path menu and takes the user's input
# Returns the path input
def set_download_path():
    
    clear_screen()
    print("""
██████╗░░█████╗░████████╗██╗░░██╗
██╔══██╗██╔══██╗╚══██╔══╝██║░░██║
██████╔╝███████║░░░██║░░░███████║
██╔═══╝░██╔══██║░░░██║░░░██╔══██║
██║░░░░░██║░░██║░░░██║░░░██║░░██║
╚═╝░░░░░╚═╝░░╚═╝░░░╚═╝░░░╚═╝░░╚═╝\n""")

    print("IMPORTANT: Input Full Path")
    print("Example: /home/{username}")
    download_path = input("\nSet Download Path: ")
    return download_path

# Clear the screen
def clear_screen():
    
    # For Windows
    if os.name == 'nt':
        os.system('cls')
    # For Linux or MacOS
    else:
        os.system('clear')

# Displays the home menu and takes user's input
# Returns the user's choice
def main_menu():
    
    clear_screen()
    print("""
██╗░░██╗░█████╗░███╗░░░███╗███████╗
██║░░██║██╔══██╗████╗░████║██╔════╝
███████║██║░░██║██╔████╔██║█████╗░░
██╔══██║██║░░██║██║╚██╔╝██║██╔══╝░░
██║░░██║╚█████╔╝██║░╚═╝░██║███████╗
╚═╝░░╚═╝░╚════╝░╚═╝░░░░░╚═╝╚══════╝

    1 - Search & Download
    2 - File Import
    3 - Edit API Keys
    4 - Exit\n""")
    choice = input("Enter: ")
    return choice

# Display the import menu and takes user's input
# Returns the user's import choice 
def import_menu():
    
    clear_screen()
    print("""
██╗███╗░░░███╗██████╗░░█████╗░██████╗░████████╗
██║████╗░████║██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝
██║██╔████╔██║██████╔╝██║░░██║██████╔╝░░░██║░░░
██║██║╚██╔╝██║██╔═══╝░██║░░██║██╔══██╗░░░██║░░░
██║██║░╚═╝░██║██║░░░░░╚█████╔╝██║░░██║░░░██║░░░
╚═╝╚═╝░░░░░╚═╝╚═╝░░░░░░╚════╝░╚═╝░░╚═╝░░░╚═╝░░░\n""")

    print("IMPORTANT: Refer to 'README.md' for file structure.")
    print("Program will run until file is completed.")

    import_choice = input("\nWould you like to continue?[y/N]: ")
    return import_choice

# Imports and parses json file given the file's path
# Returns download path and each song in the json file
def parse_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['download_path'], [(s['song_name'], s['artist_name']) for s in data['songs']]

# Displays the keys menu and takes user's input
# Updates the .env file if changes are made
# Returns True if the keys are changed and False if no keys are changed
def edit_API_keys():
    
    clear_screen()
    print("""
░█████╗░██████╗░██╗  ██╗░░██╗███████╗██╗░░░██╗░██████╗
██╔══██╗██╔══██╗██║  ██║░██╔╝██╔════╝╚██╗░██╔╝██╔════╝
███████║██████╔╝██║  █████═╝░█████╗░░░╚████╔╝░╚█████╗░
██╔══██║██╔═══╝░██║  ██╔═██╗░██╔══╝░░░░╚██╔╝░░░╚═══██╗
██║░░██║██║░░░░░██║  ██║░╚██╗███████╗░░░██║░░░██████╔╝
╚═╝░░╚═╝╚═╝░░░░░╚═╝  ╚═╝░░╚═╝╚══════╝░░░╚═╝░░░╚═════╝░\n""")
    print("Leave blank to not edit.\n")
    
    CLIENT_ID = input("Enter your Spotify CLIENT_ID: ").strip()
    CLIENT_SECRET = input("Enter your Spotify CLIENT_SECRET: ").strip()

    # Filter out the blank inputs
    if CLIENT_ID != "" and CLIENT_SECRET != "":
        # Save these to the .env file
        with open(".env", "w") as f:
            f.write(f"CLIENT_ID={CLIENT_ID}\nCLIENT_SECRET={CLIENT_SECRET}\n")
        
        # Print keys are saved and return True
        print("\nKeys saved.")
        input("\nPress enter to continue...")
        return True
    
    # Return false since no keys are changed
    else:
        return False

# Displays the error menu
def print_error_menu():
    
    clear_screen()
    print("""
███████╗██████╗░██████╗░░█████╗░██████╗░
██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔══██╗
█████╗░░██████╔╝██████╔╝██║░░██║██████╔╝
██╔══╝░░██╔══██╗██╔══██╗██║░░██║██╔══██╗
███████╗██║░░██║██║░░██║╚█████╔╝██║░░██║
╚══════╝╚═╝░░╚═╝╚═╝░░╚═╝░╚════╝░╚═╝░░╚═╝""")

# Displays a searching animation
# Loops this animation 'repeat (int param)' amount of times 
def searching_animation(repeat):
    # Frames the animation goes through
    frames = [
        "Searching   ",
        "Searching . ",
        "Searching ..",
        "Searching ...",
    ]

    # Play the animation given the amount of times by the param
    for _ in range(repeat):
        for frame in frames:
            print('\r' + frame, end='', flush=True)
            time.sleep(0.1)
    print('\r' + ' ' * 15 + '\r', end='')  # Clear the line after animation

# Displays the download menu
def print_download_menu():
    
    clear_screen()
    print("""
██████╗░░█████╗░░██╗░░░░░░░██╗███╗░░██╗██╗░░░░░░█████╗░░█████╗░██████╗░
██╔══██╗██╔══██╗░██║░░██╗░░██║████╗░██║██║░░░░░██╔══██╗██╔══██╗██╔══██╗
██║░░██║██║░░██║░╚██╗████╗██╔╝██╔██╗██║██║░░░░░██║░░██║███████║██║░░██║
██║░░██║██║░░██║░░████╔═████║░██║╚████║██║░░░░░██║░░██║██╔══██║██║░░██║
██████╔╝╚█████╔╝░░╚██╔╝░╚██╔╝░██║░╚███║███████╗╚█████╔╝██║░░██║██████╔╝
╚═════╝░░╚════╝░░░░╚═╝░░░╚═╝░░╚═╝░░╚══╝╚══════╝░╚════╝░╚═╝░░╚═╝╚═════╝░""")
    print()

# Main function that runs a loop for the main menu
def main():
    
    # Load env variables
    load_dotenv(override=True)

    # Spotify API Client Credentials
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")

    # Prompt user to enter values if missing
    if not CLIENT_ID or not CLIENT_SECRET:
        success = edit_API_keys()
        if success == True:
            load_dotenv(override=True)  # Reload environment after edit
            CLIENT_ID = os.getenv("CLIENT_ID")
            CLIENT_SECRET = os.getenv("CLIENT_SECRET")

    # Set the dwn_path out of the loop to only ask for it once
    dwn_path=""

    # While loop for the main menu
    loop=True
    while loop:
        
        # Take user's main menu choice
        choice = main_menu()
        
        # Validate the user's choice...
        # Try int convert input, throw error if not int
        try:
            choice = int(choice)
        except ValueError:
            print("Invalid Choice. Please enter a number (1-4).")
            input("Press enter to continue...")
            continue # Loop back to the main menu
        
        # Filter out input if not within range
        if choice not in [1, 2, 3, 4]:
            print("Invalid Choice. Please enter a number (1-4).")
            input("Press enter to continue...")
            continue # Loop back to the main menu

        # User input is now within range
        # Direct user to the menu chosen
        
        # Choice 1 is 'Search & Download'
        elif choice == 1:
            # Take search input
            song_name, artist_name = search_song()
            print()

            # Play the searching animation once
            searching_animation(1)

            # Try to download the song searched
            try:
                # Generate the token
                token = generate_token(CLIENT_ID,CLIENT_SECRET)
                
                # Search for the spotify song
                artist, album, song, url = search_spotify_song(token, song_name, artist_name)
                
                # If the search_spotify_song function returns 'None' catch it
                if artist == None and album == None and song == None and url == None:
                    input("Press enter to continue...")
                    continue # Loop back to the main menu
                
                # Else ask to continue to download
                down_choice = input("\nContinue to download?[y/N]: ")
                
                # Check if the url was found
                if url:

                    # Filter out user choice
                    if down_choice != "y" and down_choice != "n":
                        print()
                    
                    # If yes then continue to download
                    elif down_choice == "y":
                        
                        if dwn_path == "":
                            dwn_path = set_download_path()
                            input("\nPress enter to continue...")
                            print()
                            dest_path = set_folder(dwn_path)
                        print_download_menu()
                        song_path = create_song_folder_structure(dest_path, artist, album, song)
                        download_spotify_url(url, song_path)
                        print("Download complete!")
                        input("\nPress enter to continue...")
                        #print(f"Temp Path: {song_path}")
                    else:
                        print()
                else:
                    print("Song not found.")
                    break
            
            # If the song is unable to be searched for then print error and loop back to main menu
            except Exception as e:
                print_error_menu()
                print("\nUnable to acquire token. Check your API keys.")
                input("\nPress enter to continue...")
            
            
        # Choice 2 is 'File Import'
        elif choice == 2:
            
            # Get user choice if they want to continue with import
            import_choice = import_menu()
            
            # If the user wants to proceed else loop back to the main menu
            if import_choice == "y" or import_choice == "Y":
                
                # Prompt for import file path
                import_file_path = input("\nImport file path (example: /home/user/list.json): ")
                
                # User Confirm
                input("\nPress enter to submit path (CTL+C -> Enter to go back)...")

                # Try to parse the json file
                try:
                    path, songs = parse_json_file(import_file_path)
                
                # If file not found throw error
                except FileNotFoundError:
                    print_error_menu()
                    print(f"\nUnable find import file with path '{import_file_path}' provided.")
                    input("\nPress enter to continue...")
                    continue
                # Else throw generic error
                except Exception as e:
                    print_error_menu()
                    print(f"Error found: '{e}'")
                    input("\nPress enter to continue...")

                print()

                # Show download menu
                print_download_menu()

                # Loop through songs in the import file
                for song_name, artist_name in songs:
                    
                    # Generate token for Spotify's API
                    token = generate_token(CLIENT_ID,CLIENT_SECRET)
                    
                    # Error handle for no token generated
                    if token == None:
                        print_error_menu()
                        print("\nUnable to acquire token. Check your API keys.")
                        input("\nPress enter to exit...")
                        break # Exit the program

                    # Attempt to serach for spotify song using token
                    try:
                        artist, album, song, url = search_spotify_song(token, song_name, artist_name)
                        
                        # Check if url was found 
                        if url:
                            
                            # Set the folder found in the import file
                            try:
                                dest_path = set_folder(path)
                            
                            # Throw error if folder is unaccessable
                            except OSError as e:
                                print_error_menu()
                                print(f"\nFailed to create or access folder: {e}")
                                input("\nPress enter to exit...")
                                break # Exit program
                            
                            # Create the song's folder structure
                            song_path = create_song_folder_structure(dest_path, artist, album, song)
                            
                            # Download the song and place it in the folder strucutre
                            download_spotify_url(url, song_path)
                    
                    # Throw error menu if searching for spotify song breaks
                    except Exception as e:
                        print_error_menu()
                        print(f"\nAn error occurred: {e}")
                        input("\nPress enter to continue...")
                        continue
                
                # Print import file has been looped over
                print("Import file completed.")
                input("\nPress enter to continue...")

            # If choice was 'n' then loop back to the main menu
            elif import_choice == "n":
                print()

            # Loop back to the main menu
            elif import_choice != "y" and import_choice != "n":
                print()

        # Choice 3 is 'Edit API Keys'
        elif choice == 3:

            # Run edit API keys function and return True or False
            success = edit_API_keys()

            # If successfull reload the .env and grab the new CLIENT_ID and CLIENT_SECRET
            if success == True:
                load_dotenv(override=True)  # Reload environment after edit
                CLIENT_ID = os.getenv("CLIENT_ID")
                CLIENT_SECRET = os.getenv("CLIENT_SECRET")

            # Else success if false then loop back to the main menu

        # Choice 4 is 'exit'
        elif choice == 4:
            print()
            exit()

        # Loop back to the main menu
        else:
            print()
    
    print()
    

# Main function caller
if __name__ == "__main__":
    main()
