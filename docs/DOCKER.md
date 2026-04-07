# Docker Deployment 🐳

The Docker image starts only the Web UI:

- `apps/web/run_web_ui.py` on port `7001`

The MCP server is managed from the Web UI (Server tab) and is **not** started automatically.
Port `7000` is still published so the managed server is reachable when started from the UI.

## Build On Ubuntu 🛠️

```bash
cd /path/to/mcp-demo
docker build -f docker/Dockerfile -t mcp-demo-tool .
```

## Run Directly From Docker Hub (No Git Clone) 🚀

```bash
docker pull benoitbmtl/mcp-demo:latest

docker run -d \
  --name mcp-demo \
  --restart unless-stopped \
  -p 7000:7000 \
  -p 7001:7001 \
  benoitbmtl/mcp-demo:latest
```

## Run On Ubuntu ▶️

```bash
docker run -d \
  --name mcp-demo-tool \
  --restart unless-stopped \
  -p 7000:7000 \
  -p 7001:7001 \
  mcp-demo-tool
```

## Supported MCP Protocol Versions 📐

```text
2025-11-25
2025-06-18
2025-03-26
2024-11-05
```

## Optional Environment Variables ⚙️

```bash
docker run -d \
  --name mcp-demo-tool \
  --restart unless-stopped \
  -p 7000:7000 \
  -p 7001:7001 \
  -e WEB_UI_THEME=fortinet \
  -e WEB_UI_HOST=0.0.0.0 \
  -e WEB_UI_PORT=7001 \
  -e MCP_TOOL_DESCRIPTION_VARIANT=malicious_cryptojacking \
  -e MCP_RESOURCE_VARIANT=bias_master_slave \
  -e MCP_PROMPT_VARIANT=social_urgent \
  mcp-demo-tool
```

## Logs 📜

```bash
docker logs -f mcp-demo-tool
```

## Remove 🧹

```bash
docker rm -f mcp-demo-tool
```
