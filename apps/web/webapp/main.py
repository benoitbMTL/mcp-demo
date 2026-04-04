from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .mcp_gateway import MCPGatewayError, MCPGatewayErrorWithPayload, connect_probe, send_request
from .models import ConnectPayload, SendRequestPayload
from .request_templates import get_default_request, list_templates


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="MCP Demo Tool",
    description="Compact MCP web tool for sending raw MCP requests.",
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "templates_json": json.dumps(list_templates(), ensure_ascii=False),
            "default_request_json": json.dumps(get_default_request(), indent=2, ensure_ascii=False),
        },
    )


@app.post("/api/connect")
async def api_connect(payload: ConnectPayload) -> JSONResponse:
    try:
        result = await connect_probe(payload.target_url, payload.transport)
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
        result = await send_request(payload.target_url, payload.transport, payload.request)
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("apps.web.webapp.main:app", host="0.0.0.0", port=8000, reload=True)
