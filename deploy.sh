#!/bin/bash
# Promura Social deploy script
# Use when you want to push + redeploy from terminal without Claude.
#
# Requirements:
#   - SSH key auth set up: `ssh root@VPS_IP` works without password
#   - Local repo at $LOCAL_PATH on this Mac
#   - VPS already provisioned (Docker + compose + repo at $VPS_PATH)
#
# NOTE: When deploying through Claude/Cowork, Claude uses the MCP
# connector instead of SSH. This script is the manual-terminal fallback.

set -euo pipefail

VPS_IP="187.77.142.68"
VPS_PATH="/var/www/promura-social"
LOCAL_PATH="$HOME/projects/promura-social"
APP_PORT="8001"

echo "Deploying Promura Social..."

cd "$LOCAL_PATH"

# Commit and push latest local changes
git add -A
if git diff --cached --quiet; then
  echo "Nothing new to commit"
else
  git commit -m "deploy: $(date '+%Y-%m-%d %H:%M:%S')"
fi
git push origin main
echo "Code pushed to GitHub"

# Pull and redeploy on VPS via SSH
# Important: use BOTH compose files (base + prod), NOT prod alone.
# docker-compose.prod.yml is a supplement to docker-compose.yml.
ssh -o BatchMode=yes "root@${VPS_IP}" <<ENDSSH
  set -euo pipefail
  cd "${VPS_PATH}"
  git fetch origin
  git reset --hard origin/main
  docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
  docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T app \\
    python manage.py migrate --noinput
  docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T app \\
    python manage.py collectstatic --noinput --clear
  echo "Promura Social deployed"
ENDSSH

echo ""
echo "Live at: http://${VPS_IP}:${APP_PORT}"
echo "Admin:   http://${VPS_IP}:${APP_PORT}/admin/login/"
