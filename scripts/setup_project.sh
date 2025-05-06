#!/bin/bash
# Script to clean up and set up the pulstwin project

echo "Cleaning up any existing .egg-info directories..."
find . -name "*.egg-info" -type d -exec rm -rf {} +
find . -name "*.egg-info" -type d -exec rm -rf {} \; 2>/dev/null || true

echo "Creating __init__.py files if missing..."
for dir in src/avatar src/output src/pulse src/wearable src/wearable/sources; do
    if [ ! -f "$dir/__init__.py" ]; then
        touch "$dir/__init__.py"
        echo "Created $dir/__init__.py"
    fi
done

echo "Installing package in development mode..."
export PYTHONPATH="/Users/volker/Work/Puls/builds/install/python:$PYTHONPATH"
pip install -e .

echo ""
echo "Setup completed!"