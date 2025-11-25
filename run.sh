#!/bin/bash

# Check Python version
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
major_ver=$(echo $python_version | cut -d. -f1)
minor_ver=$(echo $python_version | cut -d. -f2)

if [ "$major_ver" -eq 3 ] && [ "$minor_ver" -ge 13 ]; then
    echo "WARNING: You are using Python $python_version. This is a very new version."
    echo "Many libraries (like pyarrow) may not have pre-built binaries for it yet."
    echo "If installation fails, please try using Python 3.10, 3.11, or 3.12."
    echo "You can install a specific version with brew: brew install python@3.11"
    echo "Then recreate the venv: rm -rf venv && python3.11 -m venv venv"
    echo "----------------------------------------------------------------"
    sleep 3
fi

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    # Try to find a suitable python if default is too new? 
    # For now, just use python3 but we warned them.
    python3 -m venv venv
    source venv/bin/activate
    
    # Check for cmake (often needed for building pyarrow/other libs from source)
    if ! command -v cmake &> /dev/null; then
        echo "Error: cmake is not installed but might be required for building dependencies."
        echo "Please install it (e.g., 'brew install cmake' on macOS) and try again."
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
