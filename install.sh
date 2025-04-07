#!/bin/bash

set -e

SERVICE_NAME="ph-streamer"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/.venv"
PYTHON_BIN="$VENV/bin/python"
MAIN_SCRIPT="$SCRIPT_DIR/main.py"
REQUIREMENTS="pyserial"

echo "📦 Installing ESP Streamer Service..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Aborting."
    exit 1
fi
if ! python3 -m venv --help > /dev/null 2>&1; then
    echo "🔧 Installing python3-venv (requires sudo)..."
    sudo apt update
    sudo apt install -y python3-venv
fi
# Create virtualenv
if [ ! -d "$VENV" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv "$VENV"
    source "$VENV/bin/activate"
    pip install --upgrade pip
    pip install $REQUIREMENTS
else
    echo "✅ Virtualenv already exists."
fi

# Install or update systemd service
if [ ! -f "$SERVICE_FILE" ]; then
    echo "🛠️ Creating systemd service..."

    cat <<EOF | sudo tee "$SERVICE_FILE"
[Unit]
Description=ESP Streamer (Auto USB + TCP + Broadcast)
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=$PYTHON_BIN $MAIN_SCRIPT
WorkingDirectory=$SCRIPT_DIR
Restart=always
RestartSec=3
User=$SUDO_USER
Environment=PYTHONUNBUFFERED=1
Environment=VIRTUAL_ENV=$VENV
Environment=PATH=$VENV/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reexec
    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"
    sudo systemctl start "$SERVICE_NAME"
    echo "✅ Service installed and started!"
else
    echo "🔁 Restarting existing service..."
    sudo systemctl daemon-reexec
    sudo systemctl daemon-reload
    sudo systemctl restart "$SERVICE_NAME"
fi


echo "🎉 Done! You can check status with:"
echo "   sudo systemctl status $SERVICE_NAME"
