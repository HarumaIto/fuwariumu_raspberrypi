#!/bin/bash

# This script sets up the necessary environment and installs dependencies.

# Exit immediately if a command exits with a non-zero status.
set -e

# Check if the virtual environment directory exists
if [ ! -d ".venv" ]; then
  echo "Virtual environment '.venv' not found. Please create it first."
  echo "You can create it using: python3 -m venv .venv"
  exit 1
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install/upgrade pip
echo "Updating pip..."
pip install --upgrade pip

# Install dependencies from requirements.txt
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "Setup complete. The virtual environment is active."
echo "To deactivate it, simply run: deactivate"
