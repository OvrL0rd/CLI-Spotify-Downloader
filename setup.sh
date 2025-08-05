#!/bin/sh
# Name: setup.sh
# Quick Desc: This script creates a virtual environment folder and installs dependencies
# Author: w1l238
# Project Link: https://github.com/w1l238/CLI-Spotify-Downloader
# Note: Run this at the root folder of the project! (i.e. in the folder 'CLI-Spotify-Downloader')


# Create a virtual environment folder named "venv" if not exists
if [ ! -d "venv" ]; then
  python3 -m venv venv
  echo "[venv] Virtual environment created."
else
  echo "[venv] Virtual environment already exists."
fi

# Activate the virtual environment and install packages
. venv/bin/activate

# If statement for install web requirements or default
read -p "Install Web Server requirements also? [y/N]: " answer
if [[ "$answer" =~ ^[Yy]$ ]]; then
    echo "[pip] Upgrading pip..."
    pip install --upgrade pip
    echo "[requirements] Installing web server requirements..."
    pip install -r WebServer/requirements.txt # Install web server requirements
else
    echo "[pip] Upgrading pip..."
    pip install --upgrade pip
    echo "[requirements] Installing CLI requirements... "
    pip install -r requirements.txt # Install CLI requirements
fi

# Download ffmpeg using spotdl
spotdl --download-ffmpeg

# TODO:
# - Move ffmpeg to the venv bin (scripts for windows). 
#   Since spotdl puts ffmpeg to user's default path. 

# Echo statements during process
# echo "Finding ffmpeg in default path..."
# echo "Moving ffmpeg from default path to virtual environment..."

# Echo that packages are installed
echo "Packages installed inside the virtual environment."
