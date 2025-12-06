#!/usr/bin/env bash
set -e

echo "🔧 Setting up virtual environment for Cisco RADKit MCP Server and tools ..."

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# Activate
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies from pyproject.toml
echo "📦 Installing dependencies from pyproject.toml..."
pip install -e ".[onboarding]"

echo "✅ Setup complete!"
clear

# Running of the onboarding utility
python radkit_onboarding.py
