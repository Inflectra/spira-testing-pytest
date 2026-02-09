#!/bin/bash

# Script to publish pytest-spiratest to PyPI

set -e  # Exit on error

echo "=================================================================="
echo "Publishing pytest-spiratest to PyPI"
echo "=================================================================="
echo ""

# Check if build and twine are installed
if ! python -c "import build" 2>/dev/null; then
    echo "❌ 'build' package not found"
    echo "Install with: pip install build"
    exit 1
fi

if ! command -v twine &> /dev/null; then
    echo "❌ 'twine' not found"
    echo "Install with: pip install twine"
    exit 1
fi

# Get version from setup.py
VERSION=$(grep "version = " setup.py | sed "s/.*version = '\(.*\)'.*/\1/")
echo "📦 Package version: $VERSION"
echo ""

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info
echo ""

# Build the package
echo "🔨 Building package..."
python -m build
echo ""

# Check the build
echo "✅ Checking package..."
twine check dist/*
echo ""

# Show what will be uploaded
echo "📋 Files to upload:"
ls -lh dist/
echo ""

# Ask for confirmation
read -p "Upload to PyPI? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Uploading to PyPI..."
    twine upload dist/*
    echo ""
    echo "=================================================================="
    echo "✅ Successfully published pytest-spiratest $VERSION to PyPI!"
    echo "=================================================================="
    echo ""
    echo "Verify with: pip install --upgrade pytest-spiratest"
else
    echo "❌ Upload cancelled"
    exit 1
fi
