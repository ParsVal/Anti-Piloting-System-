@echo off
REM Player Verification System - Quick Setup Script
REM For Windows

echo ==========================================
echo Player Verification System - Setup
echo ==========================================
echo.

REM Check Python version
python --version
if %errorlevel% neq 0 (
    echo Error: Python not found. Please install Python 3.7 or higher.
    pause
    exit /b 1
)

REM Create virtual environment (optional)
set /p create_venv="Create virtual environment? (y/n): "
if /i "%create_venv%"=="y" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Virtual environment created and activated
)

REM Install dependencies
echo.
echo Installing Python dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo Error installing dependencies
    echo You may need to install Visual Studio Build Tools
    pause
    exit /b 1
)

echo Dependencies installed successfully

REM Create necessary directories
echo.
echo Creating directory structure...
if not exist database mkdir database
if not exist logs\images mkdir logs\images
echo Directories created

REM Initialize database
echo.
echo Initializing database...
cd server
python models.py
cd ..
echo Database initialized

REM Create admin account
echo.
echo ==========================================
echo Admin Account Creation
echo ==========================================
cd scripts
python create_admin.py --interactive
cd ..

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo   1. Start the server: cd server ^&^& python app.py
echo   2. Register players: cd client ^&^& python registration_gui.py
echo   3. Access admin dashboard: http://localhost:5000/admin/login
echo.
echo For more information, see README.md
echo ==========================================
pause
