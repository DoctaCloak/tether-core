#!/bin/bash
# scripts/setup_dev_env.sh

# This script helps set up the development environment for TetherCore.
# It can be expanded to include more setup steps as needed.

# Exit immediately if a command exits with a non-zero status.
set -e

echo "🚀 Starting TetherCore Development Environment Setup..."

# --- Configuration ---
PYTHON_VERSION_TARGET="3.10" # Or your preferred Python version (e.g., 3.11)
VENV_DIR=".venv"
CONFIG_DIR="config"
EXAMPLE_CONFIG_FILE="${CONFIG_DIR}/tether_config.yaml.example"
ACTUAL_CONFIG_FILE="${CONFIG_DIR}/tether_config.yaml"
EXAMPLE_ENV_FILE=".env.example"
ACTUAL_ENV_FILE=".env"

# --- Helper Functions ---
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "❌ Error: $1 is not installed. Please install $1 and try again."
        exit 1
    fi
}

# --- Prerequisite Checks ---
echo "🔎 Checking prerequisites..."
check_command "python3"
check_command "git"
check_command "poetry" # Assuming you are using Poetry
check_command "docker"
check_command "docker-compose" # Or 'docker compose' if using Docker Compose V2

# --- Python Version Check (Basic) ---
PYTHON_VERSION_CURRENT=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "ℹ️ Current Python version: $PYTHON_VERSION_CURRENT (Target: $PYTHON_VERSION_TARGET+)"
# Add more sophisticated version checking if needed

# --- Create Virtual Environment and Install Dependencies (using Poetry) ---
if [ ! -d "$VENV_DIR" ]; then
    echo "🐍 Creating Python virtual environment using Poetry and installing dependencies..."
    poetry install --no-root # Use --no-root if tethercore itself is not installable as a library yet
    echo "✅ Poetry environment set up and dependencies installed."
else
    echo "ℹ️ Poetry virtual environment '$VENV_DIR' already exists. Skipping creation."
    echo "   To update dependencies, run 'poetry update' or 'poetry install'."
fi

# --- Setup Configuration Files ---
echo "⚙️ Setting up configuration files..."

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_DIR"

# Copy example tether_config.yaml if actual one doesn't exist
if [ -f "$EXAMPLE_CONFIG_FILE" ]; then
    if [ ! -f "$ACTUAL_CONFIG_FILE" ]; then
        cp "$EXAMPLE_CONFIG_FILE" "$ACTUAL_CONFIG_FILE"
        echo "✅ Copied '$EXAMPLE_CONFIG_FILE' to '$ACTUAL_CONFIG_FILE'. Please review and customize it."
    else
        echo "ℹ️ '$ACTUAL_CONFIG_FILE' already exists. Skipping copy."
    fi
else
    echo "⚠️ Warning: '$EXAMPLE_CONFIG_FILE' not found. Cannot create default config."
fi

# Copy example .env file if actual one doesn't exist
if [ -f "$EXAMPLE_ENV_FILE" ]; then
    if [ ! -f "$ACTUAL_ENV_FILE" ]; then
        cp "$EXAMPLE_ENV_FILE" "$ACTUAL_ENV_FILE"
        echo "✅ Copied '$EXAMPLE_ENV_FILE' to '$ACTUAL_ENV_FILE'. Please review and customize it with your secrets and local settings."
    else
        echo "ℹ️ '$ACTUAL_ENV_FILE' already exists. Skipping copy."
    fi
else
    echo "⚠️ Warning: '$EXAMPLE_ENV_FILE' not found. Cannot create default .env fil