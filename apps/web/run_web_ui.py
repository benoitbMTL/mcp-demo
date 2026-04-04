import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.web.webapp.main import app


if __name__ == "__main__":
    import os

    import uvicorn

    host = os.getenv("WEB_UI_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_UI_PORT", "7001"))
    reload_enabled = os.getenv("WEB_UI_RELOAD", "false").lower() == "true"

    uvicorn.run("apps.web.run_web_ui:app", host=host, port=port, reload=reload_enabled)
