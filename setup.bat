@echo off
setlocal

echo 🔧 Setting up virtual environment for Cisco RADKit MCP Server and tools ...

where uv >nul 2>&1
if errorlevel 1 (
    echo ❌ uv is required but not installed. Please install uv from https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

echo 📦 Syncing dependencies from pyproject.toml with uv...
uv sync --extra onboarding

echo ✅ Setup complete!
cls
uv run python radkit_onboarding.py
pause
