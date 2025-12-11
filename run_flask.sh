#!/bin/bash

# RAG Chatbot Flask Runner
# This script runs the Flask app with the improved web UI

echo "🚀 Starting RAG Chatbot with improved UI..."
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it with your GEMINI_API_KEY."
    echo "Example: GEMINI_API_KEY=your_api_key_here"
    exit 1
fi

# Install python-docx if not installed
if ! pip show python-docx > /dev/null 2>&1; then
    echo "📦 Installing python-docx for DOCX support..."
    pip install python-docx
fi

# Create data directory if it doesn't exist
mkdir -p data

# Set environment variables
export FLASK_ENV=development
export FLASK_DEBUG=1

echo "✅ Setup complete. Using Gemini API for chat."
echo "🌐 Starting Flask application..."
echo "📍 The app will be available at: http://localhost:5000"
echo "(Press Ctrl+C to stop. All uploaded files will be deleted on exit.)"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🧹 Cleaning up uploaded files..."
    if [ -d "data" ]; then
        rm -rf data/*
        echo "✅ Cleanup complete. Goodbye!"
    fi
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Start Flask app
python app_flask.py
