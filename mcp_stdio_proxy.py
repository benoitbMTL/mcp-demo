import os
import sys
import time
from fastmcp import FastMCP, Client

BACKEND_URL = os.environ.get("BACKEND_URL", "http://mcp-xperts.labsec.ca/mcp")

def run_once():
    backend = Client(BACKEND_URL)
    proxy = FastMCP.as_proxy(backend, name="MCP-XPERTS")
    proxy.run(transport="stdio")

if __name__ == "__main__":
    while True:
        try:
            run_once()
        except Exception as e:
            print(f"[proxy] crash: {e}", file=sys.stderr)
            time.sleep(2)
