#!/bin/bash

# docker build -t mcp-security-lab .

IMAGE_NAME=mcp-security-lab
CONTAINER_NAME=mcp-server
HOST_PORT=7000
CONTAINER_PORT=7000

docker run -d \
  --restart unless-stopped \
  --name ${CONTAINER_NAME} \
  -p ${HOST_PORT}:${CONTAINER_PORT} \
  ${IMAGE_NAME}
