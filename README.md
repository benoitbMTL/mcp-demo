# MCP Demo

This repository contains a complete MCP security demo with:

- a demo MCP server
- a Web UI client
- a CLI client
- Claude Desktop integration assets
- shell and PowerShell test scripts
- Docker packaging for the server + Web UI

## Repository Layout

```text
mcp-demo/
├── apps/
│   ├── cli/
│   │   └── client.py
│   └── web/
│       ├── run_web_ui.py
│       └── webapp/
├── docker/
│   ├── Dockerfile
│   └── docker-entrypoint.sh
├── docs/
│   ├── CLIENT.md
│   ├── DOCKER.md
│   └── PROMPTS.md
├── integrations/
│   └── claude-desktop/
│       ├── claude_desktop_config.json
│       └── mcp_stdio_proxy.py
├── scripts/
│   ├── mcp_tools_list.ps1
│   └── mcp_tools_list.sh
├── server/
│   ├── files/
│   ├── secrets.txt
│   └── server.py
└── requirements.txt
```

## Install

```bash
cd mcp-demo
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Makefile Shortcuts

You can use the provided `Makefile` for the most common actions:

```bash
make run-server
make run-web
make run-cli
make docker-build
make docker-run
```

Examples with overrides:

```bash
make run-server TRANSPORT=sse PROTOCOL_VERSION=2025-03-26
make run-cli TARGET_URL=http://127.0.0.1:7000/sse TRANSPORT=sse
```

## Run The MCP Server

```bash
python server/server.py --transport httpstream --host 0.0.0.0 --port 7000 --protocol-version 2025-06-18
```

Supported protocol versions:

- `2025-11-05`
- `2025-06-18`
- `2025-03-26`
- `2024-11-05`

## Run The Web UI

```bash
python apps/web/run_web_ui.py
```

Open:

```text
http://127.0.0.1:7001
```

## Run The CLI Client

```bash
python apps/cli/client.py --target-url http://mcp-xperts.labsec.ca/mcp --transport mcp
```

## Additional Documentation

- Web UI and local usage: [CLIENT.md](/home/benoitb/mcp-demo/mcp-demo/docs/CLIENT.md)
- Docker usage: [DOCKER.md](/home/benoitb/mcp-demo/mcp-demo/docs/DOCKER.md)
- Prompt examples: [PROMPTS.md](/home/benoitb/mcp-demo/mcp-demo/docs/PROMPTS.md)
