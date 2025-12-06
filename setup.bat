@echo off
echo 🔧 Setting up virtual environment for Cisco RADKit MCP Server and tools ...

if not exist .venv (
    python -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
echo 📦 Installing dependencies from pyproject.toml...
pip install -e ".[onboarding]"

echo ✅ Setup complete!
cls
python radkit_onboarding.py
pause
