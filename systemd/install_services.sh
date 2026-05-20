#!/usr/bin/env bash
set -euo pipefail

SERVICE_DIR="/etc/systemd/system"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "installing uwb-wearable.service..."
sudo cp "$REPO_DIR/systemd/uwb-wearable.service" "$SERVICE_DIR/"
sudo systemctl daemon-reload
sudo systemctl enable uwb-wearable
sudo systemctl restart uwb-wearable
sudo systemctl status uwb-wearable --no-pager || true