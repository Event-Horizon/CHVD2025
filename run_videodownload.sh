#!/bin/bash

WDIR="$(dirname "$(readlink -f "$0")")"
echo "Working Directory: $WDIR"

cd "$WDIR" || { echo "Error: Could not change to working directory."; exit 1; }

echo "Creating virtual environment..."
python3 -m venv ".venv" || { echo "Error creating virtual environment. Make sure Python3 is installed."; exit 1; }

echo "Activating virtual environment and installing dependencies..."
source "./.venv/bin/activate" || { echo "Error activating virtual environment."; exit 1; }

pip install -r "requirements.txt" || { echo "Error installing dependencies."; exit 1; }

echo "Running VideoDownload.py..."
python "VideoDownload.py"

echo "Process completed."
read -p "Press Enter to exit..."