#!/bin/bash

# Function to check if a python command is a suitable version (3.9 - 3.12)
check_python_version() {
    local cmd=$1
    if command -v "$cmd" &> /dev/null; then
        local version
        version=$($cmd -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        local major
        major=$(echo "$version" | cut -d. -f1)
        local minor
        minor=$(echo "$version" | cut -d. -f2)
        
        if [ "$major" -eq 3 ] && [ "$minor" -ge 9 ] && [ "$minor" -le 12 ]; then
            echo "$cmd"
            return 0
        fi
    fi
    return 1
}

# 1. Search for a specific suitable python version
echo "Searching for a suitable Python version (3.9 - 3.12)..."
PYTHON_CMD=""

# Check specific binaries first
for ver in 3.12 3.11 3.10 3.9; do
    if command -v "python$ver" &> /dev/null; then
        PYTHON_CMD="python$ver"
        echo "Found specific version: $PYTHON_CMD"
        break
    fi
done

# If not found, check 'python3'
if [ -z "$PYTHON_CMD" ]; then
    if check_python_version "python3" > /dev/null; then
        PYTHON_CMD="python3"
        echo "Found suitable default: $PYTHON_CMD"
    fi
fi

# 2. Handle case where no suitable version is found
if [ -z "$PYTHON_CMD" ]; then
    echo "----------------------------------------------------------------"
    echo "ERROR: No suitable Python version found (3.9 - 3.12)."
    echo "Your default 'python3' might be too new (e.g., 3.13+) or too old."
    echo ""
    echo "Please install a stable version using Homebrew:"
    echo "  brew install python@3.11"
    echo ""
    echo "After installing, run this script again."
    echo "----------------------------------------------------------------"
    exit 1
fi

# 3. Create/Activate Virtual Environment
NEEDS_INSTALL=false

if [ ! -d "venv" ]; then
    echo "Creating virtual environment using $PYTHON_CMD..."
    $PYTHON_CMD -m venv venv
    NEEDS_INSTALL=true
else
    # Check if existing venv uses a compatible Python version
    source venv/bin/activate
    venv_version=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "0.0")
    venv_major=$(echo "$venv_version" | cut -d. -f1)
    venv_minor=$(echo "$venv_version" | cut -d. -f2)
    
    if [ "$venv_major" -eq 3 ] && [ "$venv_minor" -ge 9 ] && [ "$venv_minor" -le 12 ]; then
        echo "Using existing virtual environment (Python $venv_version)..."
    else
        echo "Existing venv uses incompatible Python $venv_version. Recreating..."
        deactivate 2>/dev/null || true
        rm -rf venv
        $PYTHON_CMD -m venv venv
        source venv/bin/activate
        NEEDS_INSTALL=true
    fi
fi

# Install dependencies if needed
if [ "$NEEDS_INSTALL" = true ]; then
    # Check for cmake (helpful warning)
    if ! command -v cmake &> /dev/null; then
        echo "Warning: 'cmake' not found. Some packages might fail to build."
        echo "If installation fails, run: brew install cmake"
    fi

    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# 4. Run the App
if command -v streamlit &> /dev/null; then
    echo "Starting application..."
    streamlit run app.py
else
    echo "Error: streamlit command not found. Installation might have failed."
    exit 1
fi
