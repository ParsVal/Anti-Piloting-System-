#!/bin/bash

# Player Verification System - Quick Setup Script
# For Unix/Linux/macOS

echo "=========================================="
echo "Player Verification System - Setup"
echo "=========================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment (optional but recommended)
read -p "Create virtual environment? (y/n): " create_venv

if [ "$create_venv" = "y" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✓ Virtual environment created and activated"
fi

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "✗ Error installing dependencies"
    echo "You may need to install additional system packages:"
    echo "  Ubuntu/Debian: sudo apt-get install cmake python3-dev"
    echo "  macOS: brew install cmake"
    exit 1
fi

echo "✓ Dependencies installed successfully"

# Create necessary directories
echo ""
echo "Creating directory structure..."
mkdir -p database
mkdir -p logs/images
echo "✓ Directories created"

# Initialize database
echo ""
echo "Initializing database..."
cd server
python3 models.py
cd ..
echo "✓ Database initialized"

# Create admin account
echo ""
echo "=========================================="
echo "Admin Account Creation"
echo "=========================================="
cd scripts
python3 create_admin.py --interactive
cd ..

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Start the server: cd server && python3 app.py"
echo "  2. Register players: cd client && python3 registration_gui.py"
echo "  3. Access admin dashboard: http://localhost:5000/admin/login"
echo ""
echo "For more information, see README.md"
echo "=========================================="
