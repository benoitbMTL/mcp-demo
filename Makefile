PYTHON ?= python3
DOCKER ?= docker

TARGET_URL ?= http://mcp-xperts.labsec.ca/mcp
TRANSPORT ?= streamable-http
PROTOCOL_VERSION ?= 2025-06-18

IMAGE_NAME ?= mcp-demo-tool
CONTAINER_NAME ?= mcp-demo-tool

.PHONY: run-server run-web run-cli docker-build docker-run

run-server:
	$(PYTHON) server/server.py --transport $(TRANSPORT) --host 0.0.0.0 --port 7000 --protocol-version $(PROTOCOL_VERSION)

run-web:
	$(PYTHON) apps/web/run_web_ui.py

run-cli:
	$(PYTHON) apps/cli/client.py --target-url $(TARGET_URL) --transport $(TRANSPORT) --protocol-version $(PROTOCOL_VERSION)

docker-build:
	$(DOCKER) build -f docker/Dockerfile -t $(IMAGE_NAME) .

docker-run:
	$(DOCKER) run -d \
		--name $(CONTAINER_NAME) \
		--restart unless-stopped \
		-p 7000:7000 \
		-p 7001:7001 \
		-e MCP_TRANSPORT=$(TRANSPORT) \
		-e MCP_PROTOCOL_VERSION=$(PROTOCOL_VERSION) \
		$(IMAGE_NAME)
