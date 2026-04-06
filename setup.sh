#!/usr/bin/env bash
set -e

echo "🔧 Setting up virtual environment for Cisco RADKit MCP Server and tools ..."

if ! command -v uv >/dev/null 2>&1; then
  echo "❌ uv is required but not installed. Please install uv from https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi

# Sync dependencies from pyproject.toml
echo "📦 Syncing dependencies from pyproject.toml with uv..."
uv sync --extra onboarding

echo "✅ Setup complete!"
clear

# Running of the onboarding utility
uv run python radkit_onboarding.py
