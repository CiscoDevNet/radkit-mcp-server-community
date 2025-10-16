@echo off
echo 🔧 Setting up virtual environment for Cisco RADKit MCP Server and tools ...

if not exist venv (
    python -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo ✅ Setup complete!
venv\Scripts\activate && python radkit_onboarding.py
pause
