#!/bin/bash

echo "Starting RAGDocs Application..."
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Start the application
echo "Starting server on http://127.0.0.1:8000"
echo "Press Ctrl+C to stop the server"
echo

python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000