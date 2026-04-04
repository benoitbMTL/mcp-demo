#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-mcp-demo-tool}"
CONTAINER_NAME="${CONTAINER_NAME:-mcp-demo-tool}"
TRANSPORT="${TRANSPORT:-streamable-http}"
PROTOCOL_VERSION="${PROTOCOL_VERSION:-2025-11-25}"

if docker ps -a --format '{{.Names}}' | grep -Fxq "${CONTAINER_NAME}"; then
  echo "[INFO] Stopping existing container: ${CONTAINER_NAME}"
  docker rm -f "${CONTAINER_NAME}"
fi

echo "[INFO] Building image: ${IMAGE_NAME}"
docker build -f docker/Dockerfile -t "${IMAGE_NAME}" .

echo "[INFO] Starting container: ${CONTAINER_NAME}"
docker run -d \
  --name "${CONTAINER_NAME}" \
  --restart unless-stopped \
  -p 7000:7000 \
  -p 7001:7001 \
  -e MCP_TRANSPORT="${TRANSPORT}" \
  -e MCP_PROTOCOL_VERSION="${PROTOCOL_VERSION}" \
  "${IMAGE_NAME}"

echo "[INFO] Container is running."
