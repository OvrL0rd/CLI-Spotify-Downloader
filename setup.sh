#!/bin/sh

# Create a virtual environment folder named "venv" if not exists
if [ ! -d "venv" ]; then
  python3 -m venv venv
  echo "Virtual environment created."
else
  echo "Virtual environment already exists."
fi

# Activate the virtual environment and install packages
# This runs only within the script's subshell
. venv/bin/activate

pip install --upgrade pip
pip install requests

echo "Packages installed inside the virtual environment."