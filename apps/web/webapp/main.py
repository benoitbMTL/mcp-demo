from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .mcp_gateway import (
    DEFAULT_PROTOCOL_VERSION,
    MCPGatewayError,
    MCPGatewayErrorWithPayload,
    SUPPORTED_PROTOCOL_VERSIONS,
    connect_probe,
    disconnect_session,
    send_request_on_session,
)
from .models import ConnectPayload, DisconnectPayload, SendRequestPayload, ServerControlPayload
from .request_templates import get_default_request, list_templates
from .server_control import (
    DEFAULT_SERVER_HOST,
    DEFAULT_SERVER_PORT,
    SUPPORTED_SERVER_TRANSPORTS,
    managed_server,
)
from .themes import DEFAULT_THEME, THEME_OPTIONS, normalize_theme


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="MCP Demo Tool",
    description="Compact MCP web tool for sending raw MCP requests.",
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
ACTIVE_SESSIONS: dict[str, dict[str, Any]] = {}


def get_default_theme() -> str:
    return normalize_theme(os.getenv("WEB_UI_THEME", DEFAULT_THEME))


def get_active_session(client_session_id: str) -> dict[str, Any] | None:
    return ACTIVE_SESSIONS.get(client_session_id)


def set_active_session(client_session_id: str, session_data: dict[str, Any]) -> None:
    ACTIVE_SESSIONS[client_session_id] = session_data


def clear_active_session(client_session_id: str) -> dict[str, Any] | None:
    return ACTIVE_SESSIONS.pop(client_session_id, None)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "templates_json": json.dumps(list_templates(), ensure_ascii=False),
            "default_request_json": json.dumps(get_default_request(), indent=2, ensure_ascii=False),
            "default_theme": get_default_theme(),
            "theme_options": THEME_OPTIONS,
            "default_protocol_version": DEFAULT_PROTOCOL_VERSION,
            "protocol_version_options": SUPPORTED_PROTOCOL_VERSIONS,
            "server_transport_options": SUPPORTED_SERVER_TRANSPORTS,
            "default_server_host": DEFAULT_SERVER_HOST,
            "default_server_port": DEFAULT_SERVER_PORT,
        },
    )


@app.post("/api/connect")
async def api_connect(payload: ConnectPayload) -> JSONResponse:
    try:
        previous_session = clear_active_session(payload.client_session_id)
        if previous_session:
            await disconnect_session(
                previous_session["target_url"],
                previous_session["transport"],
                previous_session.get("mcp_session_id"),
                previous_session.get("protocol_version", DEFAULT_PROTOCOL_VERSION),
            )

        result = await connect_probe(payload.target_url, payload.transport, payload.protocol_version)
        connection = result.get("probe", {}).get("connection", {})
        set_active_session(
            payload.client_session_id,
            {
                "target_url": payload.target_url,
                "transport": payload.transport,
                "endpoint_url": result.get("endpoint_url"),
                "protocol_version": connection.get("protocol_version") or payload.protocol_version,
                "mcp_session_id": connection.get("mcp_session_id"),
            },
        )
        return JSONResponse(result)
    except MCPGatewayErrorWithPayload as exc:
        return JSONResponse(
            {
                "state": "connection_error",
                "message": str(exc),
                "waf_response": exc.payload,
            },
            status_code=400,
        )
    except MCPGatewayError as exc:
        return JSONResponse(
            {
                "state": "connection_error",
                "message": str(exc),
            },
            status_code=400,
        )
    except Exception as exc:
        return JSONResponse(
            {
                "state": "connection_error",
                "message": f"{exc.__class__.__name__}: {exc}",
            },
            status_code=502,
        )


@app.post("/api/send")
async def api_send(payload: SendRequestPayload) -> JSONResponse:
    try:
        active_session = get_active_session(payload.client_session_id)
        if not active_session:
            return JSONResponse(
                {
                    "ok": False,
                    "message": "No active session. Connect first.",
                },
                status_code=400,
            )

        if (
            active_session["target_url"] != payload.target_url
            or active_session["transport"] != payload.transport
            or active_session.get("protocol_version") != payload.protocol_version
        ):
            return JSONResponse(
                {
                    "ok": False,
                    "message": "Target URL, transport, or protocol version changed. Disconnect and reconnect first.",
                },
                status_code=400,
            )

        result = await send_request_on_session(
            payload.target_url,
            payload.transport,
            payload.request,
            active_session.get("mcp_session_id"),
            active_session.get("protocol_version", payload.protocol_version),
        )
        return JSONResponse(
            {
                "ok": True,
                "result": result,
            }
        )
    except MCPGatewayErrorWithPayload as exc:
        return JSONResponse(
            {
                "ok": False,
                "message": str(exc),
                "waf_response": exc.payload,
            },
            status_code=400,
        )
    except MCPGatewayError as exc:
        return JSONResponse(
            {
                "ok": False,
                "message": str(exc),
            },
            status_code=400,
        )
    except Exception as exc:
        return JSONResponse(
            {
                "ok": False,
                "message": f"{exc.__class__.__name__}: {exc}",
            },
            status_code=502,
        )


@app.post("/api/disconnect")
async def api_disconnect(payload: DisconnectPayload) -> JSONResponse:
    active_session = clear_active_session(payload.client_session_id)
    if not active_session:
        return JSONResponse(
            {
                "ok": True,
                "disconnected": True,
                "message": "No active session.",
            }
        )

    try:
        result = await disconnect_session(
            active_session["target_url"],
            active_session["transport"],
            active_session.get("mcp_session_id"),
            active_session.get("protocol_version", payload.protocol_version),
        )
        return JSONResponse(
            {
                "ok": True,
                "result": result,
            }
        )
    except MCPGatewayError as exc:
        return JSONResponse(
            {
                "ok": False,
                "message": str(exc),
            },
            status_code=400,
        )
    except Exception as exc:
        return JSONResponse(
            {
                "ok": False,
                "message": f"{exc.__class__.__name__}: {exc}",
            },
            status_code=502,
        )


@app.get("/api/server/status")
async def api_server_status() -> JSONResponse:
    return JSONResponse(
        {
            "ok": True,
            "status": managed_server.status(),
            "logs": managed_server.tail_logs(),
        }
    )


@app.post("/api/server/start")
async def api_server_start(payload: ServerControlPayload) -> JSONResponse:
    try:
        status = managed_server.start(
            transport=payload.transport,
            protocol_version=payload.protocol_version,
            host=payload.host,
            port=payload.port,
        )
        return JSONResponse({"ok": True, "status": status, "logs": managed_server.tail_logs()})
    except Exception as exc:
        return JSONResponse(
            {
                "ok": False,
                "message": f"{exc.__class__.__name__}: {exc}",
                "status": managed_server.status(),
                "logs": managed_server.tail_logs(),
            },
            status_code=400,
        )


@app.post("/api/server/stop")
async def api_server_stop() -> JSONResponse:
    try:
        status = managed_server.stop()
        return JSONResponse({"ok": True, "status": status, "logs": managed_server.tail_logs()})
    except Exception as exc:
        return JSONResponse(
            {
                "ok": False,
                "message": f"{exc.__class__.__name__}: {exc}",
                "status": managed_server.status(),
                "logs": managed_server.tail_logs(),
            },
            status_code=400,
        )


@app.post("/api/server/restart")
async def api_server_restart(payload: ServerControlPayload) -> JSONResponse:
    try:
        status = managed_server.restart(
            transport=payload.transport,
            protocol_version=payload.protocol_version,
            host=payload.host,
            port=payload.port,
        )
        return JSONResponse({"ok": True, "status": status, "logs": managed_server.tail_logs()})
    except Exception as exc:
        return JSONResponse(
            {
                "ok": False,
                "message": f"{exc.__class__.__name__}: {exc}",
                "status": managed_server.status(),
                "logs": managed_server.tail_logs(),
            },
            status_code=400,
        )


@app.post("/api/server/logs/reset")
async def api_server_logs_reset() -> JSONResponse:
    return JSONResponse(
        {
            "ok": True,
            "status": managed_server.status(),
            "logs": managed_server.clear_logs(),
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("apps.web.webapp.main:app", host="0.0.0.0", port=8000, reload=True)
