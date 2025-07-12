#!/bin/bash

# Secret Run Installation Script
# This script installs secret-run and its dependencies

set -e

echo "🚀 Installing Secret Run..."
echo "=========================="

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.10 or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -e ".[dev,all]"

# Install pre-commit hooks
echo "🔗 Installing pre-commit hooks..."
pre-commit install

# Create configuration directory
echo "⚙️  Setting up configuration..."
mkdir -p ~/.config/secret-run/{profiles,templates,logs}

# Test installation
echo "🧪 Testing installation..."
python -c "import secret_run; print('✅ Secret Run imported successfully')"

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "To get started:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run secret-run: secret-run --help"
echo "3. Try the example: secret-run run 'echo Hello World' --env TEST=value"
echo ""
echo "For more information, see the README.md file." 