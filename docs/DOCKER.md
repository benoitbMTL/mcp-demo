# Docker Deployment 🐳

This Docker setup includes 2 components:

- Web UI (`apps/web/run_web_ui.py`) on port `7001`
- MCP server (`server/server.py`) on port `7000`, managed from the Web UI (**Server** tab)

The MCP server is not started automatically with the container. Start it from the Web UI when needed.

## Build And Run From GitHub (Ubuntu) 🛠️▶️

```bash
git clone https://github.com/benoitbMTL/mcp-demo.git
cd mcp-demo

docker build -f docker/Dockerfile -t mcp-demo .

docker run -d \
  --name mcp-demo \
  --restart unless-stopped \
  -p 7000:7000 \
  -p 7001:7001 \
  mcp-demo
```

## Run Directly From Docker Hub (No Git Clone) 🚀

```bash
docker run -d \
  --name mcp-demo \
  --restart unless-stopped \
  -p 7000:7000 \
  -p 7001:7001 \
  benoitbmtl/mcp-demo:latest
```

## Supported MCP Protocol Versions 📐

```text
2025-11-25
2025-06-18
2025-03-26
2024-11-05
```

## Optional Environment Variables ⚙️

| Variable | Possible values | Default |
|---|---|---|
| `WEB_UI_THEME` | `neo-brutalism`, `glassmorphism`, `bootstrap-light`, `glassbox-dark`, `fortinet` | `neo-brutalism` |
| `WEB_UI_HOST` | Any bind host/IP, for example `0.0.0.0`, `127.0.0.1` | `0.0.0.0` |
| `WEB_UI_PORT` | Any valid TCP port (for example `7001`) | `7001` |
| `WEB_UI_RELOAD` | `true`, `false` | `false` |
| `MCP_TOOL_DESCRIPTION_VARIANT` | `benign`, `malicious_cryptojacking`, `social_urgent`, `code_shell_rmrf` | `malicious_cryptojacking` |
| `MCP_RESOURCE_VARIANT` | `benign`, `bias_master_slave`, `exfil_ssn`, `exfil_url` | `bias_master_slave` |
| `MCP_PROMPT_VARIANT` | `benign`, `malicious_cryptojacking`, `social_urgent`, `code_shell_rmrf` | `social_urgent` |

Example:

```bash
docker run -d \
  --name mcp-demo \
  --restart unless-stopped \
  -p 7000:7000 \
  -p 7001:7001 \
  -e WEB_UI_THEME=fortinet \
  -e WEB_UI_HOST=0.0.0.0 \
  -e WEB_UI_PORT=7001 \
  -e WEB_UI_RELOAD=false \
  -e MCP_TOOL_DESCRIPTION_VARIANT=malicious_cryptojacking \
  -e MCP_RESOURCE_VARIANT=bias_master_slave \
  -e MCP_PROMPT_VARIANT=social_urgent \
  benoitbmtl/mcp-demo:latest
```

## Logs 📜

```bash
docker logs -f mcp-demo
```

## Stop And Remove 🧹

```bash
docker stop mcp-demo
docker rm mcp-demo
```

