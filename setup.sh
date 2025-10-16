#!/usr/bin/env bash
set -e

echo "🔧 Setting up virtual environment for Cisco RADKit MCP Server and tools ..."

# Create venv if it doesn’t exist
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# Activate
source .venv/bin/activate

# Upgrade pip and install deps
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Setup complete!"
clear

# Running of the onboarding utility
python radkit_onboarding.py
