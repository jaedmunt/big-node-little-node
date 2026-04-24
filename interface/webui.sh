#!/usr/bin/env bash
# Pulls and runs Open WebUI (slim image) on http://localhost:3000.
# Point it at the router endpoints in Settings > Connections.
#
# Stop with: docker stop open-webui && docker rm open-webui

set -euo pipefail

IMAGE="ghcr.io/open-webui/open-webui:main-slim"

echo "Starting Open WebUI..."
echo ""

if ! docker image inspect "$IMAGE" &>/dev/null; then
    echo "Pulling $IMAGE (first run only)..."
    docker pull "$IMAGE"
fi

# Stop any previous container with the same name.
docker rm -f open-webui &>/dev/null || true

docker run -d \
    --name open-webui \
    -p 3000:8080 \
    -e WEBUI_AUTH=false \
    -v open-webui:/app/backend/data \
    "$IMAGE"

echo "Open WebUI running at http://localhost:3000"
echo "Add your router endpoints under Settings > Connections."
echo "Stop: docker stop open-webui && docker rm open-webui"
