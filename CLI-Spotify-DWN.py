# This program will be able to...
# - Search and Download Spotify Songs
# - Specify folder to place songs into
# - Make folder structure for each song as follows:
#   Song artist
#    L Song Playlist
#       L Song Name (Song Name - Artist Name.mp3)
#
# - Mass download via json file importing
# - Edit API keys

import os
import re
import requests
import subprocess
import sys
import time
import json
from dotenv import load_dotenv

# Get API token using Client ID and Client Secret
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
def search_spotify_song(access_token, song_name, artist_name):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    query = f"track:{song_name} artist:{artist_name}"
    params = {
        "q": query,
        "type": "track",
        "limit": 1
    }
    search_url = "https://api.spotify.com/v1/search"

    response = requests.get(search_url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Spotify API search failed: {response.status_code} {response.text}")
        return None, None, None, None

    results = response.json()
    tracks = results.get("tracks", {}).get("items", [])
    if not tracks:
        print(f"No matching tracks found for '{song_name}' by '{artist_name}'.")
        return None, None, None, None

    track = tracks[0]
    track_name = track["name"]
    track_artist = ", ".join(artist["name"] for artist in track["artists"])
    album_name = track["album"]["name"]
    track_url = track["external_urls"]["spotify"]

    print(f"'{track_name}' by {track_artist} on album '{album_name}' found.")
    #print(f"Spotify URL: {track_url}")

    return track_artist, album_name, track_name, track_url

    
    response = requests.get(search_url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Spotify API search failed: {response.status_code} {response.text}")
        return None
    
    results = response.json()
    tracks = results.get("tracks", {}).get("items", [])
    if not tracks:
        print(f"No matching tracks found for '{song_name}' by '{artist_name}'.")
        return None

    track = tracks[0]
    track_name = track["name"]
    track_artist = ", ".join(artist["name"] for artist in track["artists"])
    track_url = track["external_urls"]["spotify"]

    print(f"Found song: '{track_name}' by {track_artist}")
    print(f"Spotify URL: {track_url}")
    return track_url


# Setting destination folder function given path
def set_folder(givn_folder):
    if not os.path.exists(givn_folder): # If folder doesn't exist. Make it
        os.makedirs(givn_folder)
        #print(f"Folder made at '{givn_folder}'")
        print(f"\nCreating folder '{givn_folder}'...")
        return givn_folder
    else:
        #print(f"Folder already found at '{givn_folder}'. No changes needed.")
        return givn_folder


# Download sepcific song function given path using spotDL
def download_spotify_url(spotify_url, output_folder):
    command = [sys.executable, "-m", "spotdl", spotify_url]
    
    if output_folder:
        command.extend(["--output", output_folder])
    
    try:
        subprocess.check_call(command)
        #print(f"Downloaded from {spotify_url} successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error during download: {e}")

def sanitize_filename(name):
    # Remove illegal characters for file/folder names
    return re.sub(r'[<>:"/\\|?*\n\r\t]', "_", name).strip()

# Create song folder structure function given song, album, and artist
def create_song_folder_structure(dest_path, artist, playlist, song_name):
    # artist_folder = os.path.join(dest_path, artist)
    # playlist_folder = os.path.join(artist_folder, playlist)
    # os.makedirs(playlist_folder, exist_ok=True)
    
    # song_file_path = os.path.join(playlist_folder)
    # return song_file_path

    safe_artist = sanitize_filename(artist)
    safe_playlist = sanitize_filename(playlist)
    artist_folder = os.path.join(dest_path, safe_artist)
    playlist_folder = os.path.join(artist_folder, safe_playlist)
    os.makedirs(playlist_folder, exist_ok=True)
    return playlist_folder


# Function that displays the main menu
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

# Function that sets download path
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

def clear_screen():
    # For Windows
    if os.name == 'nt':
        os.system('cls')
    # For Linux or MacOS
    else:
        os.system('clear')


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
    4 - Exit
    \n""")
    choice = input("Enter: ")
    return choice


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

# Imports and parses json file and returns to download each song specified
def parse_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['download_path'], [(s['song_name'], s['artist_name']) for s in data['songs']]


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

    if CLIENT_ID != "" and CLIENT_SECRET != "":
        # Save these to the .env file
        with open(".env", "w") as f:
            f.write(f"CLIENT_ID={CLIENT_ID}\nCLIENT_SECRET={CLIENT_SECRET}\n")

        print("\nKeys saved.")
        input("\nPress enter to continue...")
        return True
    else:
        return False


def print_error_menu():
    clear_screen()
    print("""
███████╗██████╗░██████╗░░█████╗░██████╗░
██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔══██╗
█████╗░░██████╔╝██████╔╝██║░░██║██████╔╝
██╔══╝░░██╔══██╗██╔══██╗██║░░██║██╔══██╗
███████╗██║░░██║██║░░██║╚█████╔╝██║░░██║
╚══════╝╚═╝░░╚═╝╚═╝░░╚═╝░╚════╝░╚═╝░░╚═╝""")


def searching_animation(repeat):
    frames = [
        "Searching   ",
        "Searching . ",
        "Searching ..",
        "Searching ...",
    ]

    for _ in range(repeat):
        for frame in frames:
            print('\r' + frame, end='', flush=True)
            time.sleep(0.1)
    print('\r' + ' ' * 15 + '\r', end='')  # Clear the line after animation

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

    dwn_path=""
    loop=True
    while loop:
        choice = main_menu()
        try:
            choice = int(choice)
        except ValueError:
            print("Invalid Choice. Please enter a number (1-4).")
            input("Press enter to continue...")
            continue
        if choice not in [1, 2, 3, 4]:
            print("Invalid Choice. Please enter a number (1-4).")
            input("Press enter to continue...")
            continue

        elif choice == 1:
            song_name, artist_name = search_song()
            print()

            # Put searching animation here.
            searching_animation(1)

            try:
                token = generate_token(CLIENT_ID,CLIENT_SECRET)
                artist, album, song, url = search_spotify_song(token, song_name, artist_name)
                if artist == None and album == None and song == None and url == None:
                    input("Press enter to continue...")
                    continue
                down_choice = input("\nContinue to download?[y/N]: ")
                if url:    
                    if down_choice != "y" and down_choice != "n":
                        print()
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
            
            except:
                print_error_menu()
                print("\nUnable to acquire token. Check your API keys.")
                input("\nPress enter to continue...")
            
            

        elif choice == 2:
            import_choice = import_menu()
            if import_choice == "y":
                
                import_file_path = input("\nImport file path (example: /home/user/list.json): ")
                try:
                    input("\nPress enter to submit path (CTL+C -> Enter to go back)...")
                    path, songs = parse_json_file(import_file_path)
                except:
                    print_error_menu()
                    print(f"\nUnable find import file with path '{import_file_path}' provided.")
                    input("\nPress enter to continue...")
                    continue
                print()
                
                # try:
                #     for song_name, artist_name in songs:
                #         #print(f"Song Name: {song_name}, Artist Name: {artist_name}")
                #         token = generate_token(CLIENT_ID,CLIENT_SECRET)
                #         artist, album, song, url = search_spotify_song(token, song_name, artist_name)
                #         if url:
                #             dest_path = set_folder(path)
                #             song_path = create_song_folder_structure(dest_path, artist, album, song)
                #             download_spotify_url(url, song_path)
                #     print("Import file completed!\n")
                #     input("Press enter to continue...")

                # except:
                #     print_error_menu()
                #     print("\nUnable to acquire token. Check your API keys.")
                #     input("\nPress enter to continue...")


                print_download_menu()
                for song_name, artist_name in songs:
                    
                    token = generate_token(CLIENT_ID,CLIENT_SECRET)
                    if token == None:
                        print_error_menu()
                        print("\nUnable to acquire token. Check your API keys.")
                        input("\nPress enter to continue...")
                        break

                    try:
                        artist, album, song, url = search_spotify_song(token, song_name, artist_name)
                        if url:
                            try:
                                dest_path = set_folder(path)
                            except OSError as e:
                                print_error_menu()
                                print(f"\nFailed to create or access folder: {e}")
                                input("\nPress enter to continue...")
                                break

                            song_path = create_song_folder_structure(dest_path, artist, album, song)
                            download_spotify_url(url, song_path)
                    except Exception as e:
                        print_error_menu()
                        print(f"\nAn error occurred: {e}")
                        input("\nPress enter to continue...")
                        continue
                
                if token != None and artist != None and album != None and song != None and url != None:
                    print("Import file completed!")
                    input("\nPress enter to continue...")
                elif artist == None and album == None and song == None and url == None:
                    input("\nPress enter to continue...")
                else:
                    input("\nPress enter to continue...")

            # except:
            #     print_error_menu()
            #     print("\nUnable to acquire token. Check your API keys.")
            #     input("\nPress enter to continue...")




            elif import_choice == "n":
                print()

            elif import_choice != "y" and import_choice != "n":
                print()

        elif choice == 3:
            success = edit_API_keys()
            if success == True:
                load_dotenv(override=True)  # Reload environment after edit
                CLIENT_ID = os.getenv("CLIENT_ID")
                CLIENT_SECRET = os.getenv("CLIENT_SECRET")

        elif choice == 4:
            print()
            exit()

        else:
            print()
    
    print()
    

if __name__ == "__main__":
    main()
