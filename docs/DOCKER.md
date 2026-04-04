# Docker Deployment

The Docker image runs both services in one container:

- `server/server.py` on port `7000`
- `apps/web/run_web_ui.py` on port `7001`

## Build On Ubuntu

```bash
cd /path/to/mcp-demo
docker build -f docker/Dockerfile -t mcp-demo-tool .
```

## Run On Ubuntu

```bash
docker run -d \
  --name mcp-demo-tool \
  --restart unless-stopped \
  -p 7000:7000 \
  -p 7001:7001 \
  -e MCP_PROTOCOL_VERSION=2025-06-18 \
  mcp-demo-tool
```

## Supported MCP Protocol Versions

```text
2025-11-05
2025-06-18
2025-03-26
2024-11-05
```

## Optional Environment Variables

```bash
docker run -d \
  --name mcp-demo-tool \
  --restart unless-stopped \
  -p 7000:7000 \
  -p 7001:7001 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PROTOCOL_VERSION=2025-06-18 \
  -e MCP_TOOL_DESCRIPTION_VARIANT=malicious_cryptojacking \
  -e MCP_RESOURCE_VARIANT=bias_master_slave \
  -e MCP_PROMPT_VARIANT=social_urgent \
  mcp-demo-tool
```

## Logs

```bash
docker logs -f mcp-demo-tool
```

## Remove

```bash
docker rm -f mcp-demo-tool
```
