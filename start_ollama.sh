#!/bin/bash

echo "🚀 Starting Ollama for Local Model Usage"
echo "=========================================="

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Error: Ollama is not installed"
    echo ""
    echo "To install Ollama:"
    echo "  brew install ollama"
    echo ""
    echo "Or visit: https://ollama.ai/download"
    exit 1
fi

# Check if already running
if pgrep -x "ollama" > /dev/null; then
    echo "✓ Ollama is already running"
else
    echo "Starting Ollama service..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
    echo "✓ Ollama service started"
fi

# Check for required model
REQUIRED_MODEL="llama3.2:1b"
echo ""
echo "Checking for model: $REQUIRED_MODEL"

if ollama list | grep -q "$REQUIRED_MODEL"; then
    echo "✓ Model is already downloaded"
else
    echo "⬇️  Downloading model (this may take a few minutes)..."
    ollama pull "$REQUIRED_MODEL"
    
    if [ $? -eq 0 ]; then
        echo "✅ Model downloaded successfully!"
    else
        echo "❌ Failed to download model"
        exit 1
    fi
fi

echo ""
echo "✅ Ollama is ready!"
echo "You can now select 'Local (Ollama)' in the chatbot sidebar."
