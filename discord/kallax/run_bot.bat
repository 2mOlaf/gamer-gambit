@echo off
echo Starting Kallax Discord Bot...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found
    echo Please copy .env.example to .env and configure your Discord token
    echo.
    pause
)

REM Install dependencies if needed
echo Checking dependencies...
pip install -r requirements.txt --quiet

REM Run the bot
echo Starting bot...
echo.
python bot.py

pause
