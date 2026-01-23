#!/bin/bash

echo "=========================================="
echo "Fabric CI/CD Setup Script"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "Found Python version: $PYTHON_VERSION"
echo ""

# Check Node.js version
echo "Checking Node.js version..."
if ! command -v node &> /dev/null; then
    echo "Warning: Node.js is not installed. MCP servers require Node.js."
    echo "Please install Node.js from https://nodejs.org/"
else
    NODE_VERSION=$(node --version)
    echo "Found Node.js version: $NODE_VERSION"
fi
echo ""

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
echo "Virtual environment created."
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip
echo ""

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt
echo "Dependencies installed."
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.template .env
    echo ".env file created. Please edit it with your credentials."
    echo ""
fi

echo "=========================================="
echo "Setup completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit the .env file with your Azure/Fabric credentials"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Start using the Fabric CLI: fabric-cli --help"
echo ""
echo "For MCP server configuration, see .mcp/config.json"
echo ""
