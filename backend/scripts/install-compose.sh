#!/bin/bash
# Install docker-compose plugin on CachyOS/Arch
# Run with: sudo bash scripts/install-compose.sh
set -e
pacman -S --noconfirm docker-compose
echo "docker compose plugin installed."
echo "Now run: sudo bash scripts/setup-test-db.sh"
