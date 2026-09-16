#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/think-code-mediabot"
REPO_URL="https://github.com/YOUR_USERNAME/think-code-mediabot.git"

echo "=== Installing system deps ==="
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-venv git

echo "=== Cloning repo ==="
sudo mkdir -p "$APP_DIR"
sudo chown "$USER":"$USER" "$APP_DIR"
git clone "$REPO_URL" "$APP_DIR"

echo "=== Setting up venv ==="
python3 -m venv "$APP_DIR/.venv"
source "$APP_DIR/.venv/bin/activate"
pip install -r "$APP_DIR/requirements.txt"

echo "=== Copying .env ==="
if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo ""
    echo ">>> EDIT $APP_DIR/.env with your secrets <<<"
    echo ""
fi

echo "=== Installing systemd service ==="
sudo cp "$APP_DIR/scripts/mediabot.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mediabot

echo ""
echo "Done. Next steps:"
echo "  1. nano $APP_DIR/.env   (fill in your secrets)"
echo "  2. sudo systemctl start mediabot"
echo "  3. sudo systemctl status mediabot"
