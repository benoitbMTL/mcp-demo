import sys
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.web.webapp.themes import DEFAULT_THEME, THEME_OPTIONS


if __name__ == "__main__":
    import os

    import uvicorn

    parser = argparse.ArgumentParser(description="Run the MCP Demo Web UI.")
    parser.add_argument(
        "--theme",
        choices=[theme["id"] for theme in THEME_OPTIONS],
        default=os.getenv("WEB_UI_THEME", DEFAULT_THEME),
        help="Default visual theme for the Web UI.",
    )
    args = parser.parse_args()

    os.environ["WEB_UI_THEME"] = args.theme
    host = os.getenv("WEB_UI_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_UI_PORT", "7001"))
    reload_enabled = os.getenv("WEB_UI_RELOAD", "false").lower() == "true"

    uvicorn.run("apps.web.webapp.main:app", host=host, port=port, reload=reload_enabled)
