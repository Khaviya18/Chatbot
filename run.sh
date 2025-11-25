#!/bin/bash

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    # Check for cmake (often needed for building pyarrow/other libs from source)
    if ! command -v cmake &> /dev/null; then
        echo "Error: cmake is not installed but might be required for building dependencies."
        echo "Please install it (e.g., 'brew install cmake' on macOS) and try again."
        # We don't exit here because sometimes wheels exist and cmake isn't needed, 
        # but if pip fails later, the user will have seen this warning.
    fi

    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run the app
if command -v streamlit &> /dev/null; then
    streamlit run app.py
else
    echo "Error: streamlit command not found. Installation might have failed."
    exit 1
fi
