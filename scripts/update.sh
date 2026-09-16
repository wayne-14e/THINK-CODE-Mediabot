#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/think-code-mediabot"
source "$APP_DIR/.venv/bin/activate"

cd "$APP_DIR"
git pull
pip install -r requirements.txt
sudo systemctl restart mediabot
echo "Updated and restarted."
