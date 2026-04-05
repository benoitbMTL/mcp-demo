# Clients 🧭

This project includes two client entrypoints:

- Web UI: `apps/web/run_web_ui.py`
- CLI: `apps/cli/client.py`

## Install 🛠️

```bash
cd /path/to/mcp-demo
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Start The MCP Server Locally 🖥️

```bash
python server/server.py --transport streamable-http --host 0.0.0.0 --port 7000 --protocol-version 2025-11-25
```

## Start The Web UI 🌐

```bash
python apps/web/run_web_ui.py --theme neo-brutalism
```

Supported themes:

- `neo-brutalism` → `Neo Brutalism`
- `glassmorphism` → `Glassmorphism`
- `bootstrap-light` → `Bootstrap Light`
- `glassbox-dark` → `Glassbox Dark`
- `fortinet` → `Fortinet`

Then open:

```text
http://127.0.0.1:7001
```

## Start The CLI Client 💻

```bash
python apps/cli/client.py --target-url http://127.0.0.1:7000/mcp --transport streamable-http --protocol-version 2025-11-25
```

For SSE:

```bash
python apps/cli/client.py --target-url http://127.0.0.1:7000/sse --transport sse --protocol-version 2025-11-25
```
