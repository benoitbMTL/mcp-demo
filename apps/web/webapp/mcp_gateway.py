from __future__ import annotations

import asyncio
import contextlib
import json
import re
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

import httpx


DEFAULT_PROTOCOL_VERSION = "2025-11-25"
SUPPORTED_PROTOCOL_VERSIONS = ["2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05"]
DEFAULT_HEADERS = {"Authorization": "Bearer token"}
MCP_SESSION_ID_HEADER = "mcp-session-id"
SSE_ACCEPT_HEADER = "text/event-stream"
JSON_ACCEPT_HEADER = "application/json, text/event-stream"
RETRYABLE_HTTP_ERRORS = (httpx.RemoteProtocolError, httpx.ReadError, httpx.WriteError)


class MCPGatewayError(Exception):
    """Raised when connection setup or request execution fails."""


def parse_json_loose(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        cleaned = re.sub(r",(\s*[}\]])", r"\1", text)
        return json.loads(cleaned)


def normalize_transport(transport: str) -> str:
    if transport == "sse":
        return "sse"
    if transport == "streamable-http":
        return "streamable-http"
    raise MCPGatewayError(f"Unsupported transport: {transport}")


def build_endpoint_url(target_url: str, transport: str) -> str:
    cleaned = target_url.strip().rstrip("/")
    if not cleaned:
        raise MCPGatewayError("Target URL is required.")

    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise MCPGatewayError(
            "Target URL must start with http:// or https:// and include a host."
        )

    normalize_transport(transport)
    return parsed._replace(params="", query="", fragment="").geturl()


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def make_initialize_request(protocol_version: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": "connect-init",
        "method": "initialize",
        "params": {
            "protocolVersion": protocol_version,
            "capabilities": {},
            "clientInfo": {
                "name": "mcp-demo-web-ui",
                "version": "1.0",
            },
        },
    }


def make_initialized_notification() -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {},
    }


def extract_request_id(payload: Any) -> str | int | None:
    if isinstance(payload, dict):
        return payload.get("id")
    return None


def extract_sse_session_id(message_url: str) -> str | None:
    parsed_url = urlparse(message_url)
    query_params = parse_qs(parsed_url.query)
    for key in ("session_id", "sessionId", "mcp_session_id", "mcp-session-id", "token"):
        values = query_params.get(key)
        if values:
            return values[0]
    return None


def parse_http_response(response: httpx.Response) -> dict[str, Any]:
    content_type = response.headers.get("content-type", "")
    body_text = response.text
    parsed_body: Any
    if "application/json" in content_type:
        try:
            parsed_body = parse_json_loose(body_text)
        except json.JSONDecodeError:
            parsed_body = body_text
    elif "text/event-stream" in content_type:
        parsed_body = parse_sse_body(body_text)
    else:
        try:
            parsed_body = parse_json_loose(body_text)
        except json.JSONDecodeError:
            parsed_body = body_text

    payload = {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "content_type": content_type,
        "body": to_jsonable(parsed_body),
    }
    if response.headers.get(MCP_SESSION_ID_HEADER):
        payload["mcp_session_id"] = response.headers.get(MCP_SESSION_ID_HEADER)
    return payload


def parse_sse_body(body_text: str) -> Any:
    events: list[dict[str, Any]] = []
    event_name = "message"
    data_lines: list[str] = []

    for line in body_text.splitlines():
        if line.startswith("event:"):
            event_name = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data_lines.append(line.split(":", 1)[1].lstrip())
        elif line.strip() == "":
            if data_lines:
                data_text = "\n".join(data_lines)
                try:
                    parsed_data: Any = parse_json_loose(data_text)
                except json.JSONDecodeError:
                    parsed_data = data_text
                events.append(
                    {
                        "event": event_name,
                        "data": parsed_data,
                    }
                )
            event_name = "message"
            data_lines = []

    if data_lines:
        data_text = "\n".join(data_lines)
        try:
            parsed_data = parse_json_loose(data_text)
        except json.JSONDecodeError:
            parsed_data = data_text
        events.append(
            {
                "event": event_name,
                "data": parsed_data,
            }
        )

    if len(events) == 1 and events[0]["event"] == "message":
        return events[0]["data"]
    if events:
        return events
    return body_text


async def send_http_request(
    client: httpx.AsyncClient,
    endpoint_url: str,
    payload: Any,
    protocol_version: str,
    session_id: str | None = None,
) -> dict[str, Any]:
    headers = {
        **DEFAULT_HEADERS,
        "Accept": JSON_ACCEPT_HEADER,
        "Content-Type": "application/json",
        "Connection": "close",
        "mcp-protocol-version": protocol_version,
    }
    if session_id:
        headers[MCP_SESSION_ID_HEADER] = session_id

    response = await post_with_retry(
        client,
        endpoint_url,
        content=json.dumps(payload, ensure_ascii=False),
        headers=headers,
    )
    return parse_http_response(response)


async def delete_http_session(
    client: httpx.AsyncClient,
    endpoint_url: str,
    session_id: str,
    protocol_version: str,
) -> dict[str, Any]:
    response = await client.request(
        "DELETE",
        endpoint_url,
        headers={
            **DEFAULT_HEADERS,
            "Accept": JSON_ACCEPT_HEADER,
            "Connection": "close",
            "mcp-protocol-version": protocol_version,
            MCP_SESSION_ID_HEADER: session_id,
        },
    )
    return parse_http_response(response)


async def post_with_retry(
    client: httpx.AsyncClient,
    endpoint_url: str,
    *,
    content: str,
    headers: dict[str, str],
    attempts: int = 3,
) -> httpx.Response:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return await client.post(
                endpoint_url,
                content=content,
                headers=headers,
            )
        except RETRYABLE_HTTP_ERRORS as exc:
            last_error = exc
            if attempt == attempts:
                break
            await asyncio.sleep(0.2 * attempt)
    raise MCPGatewayError(
        "RemoteProtocolError: peer closed connection before completing the response."
    ) from last_error


async def read_sse_events(response: httpx.Response, queue: asyncio.Queue) -> None:
    event_name = "message"
    data_lines: list[str] = []

    async for line in response.aiter_lines():
        if line.startswith("event:"):
            event_name = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data_lines.append(line.split(":", 1)[1].lstrip())
        elif line == "":
            await queue.put(
                {
                    "event": event_name,
                    "data": "\n".join(data_lines),
                }
            )
            event_name = "message"
            data_lines = []


async def wait_for_sse_event(
    queue: asyncio.Queue,
    *,
    event_name: str | None = None,
    request_id: str | int | None = None,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    while True:
        event = await asyncio.wait_for(queue.get(), timeout=timeout_seconds)
        if event_name is not None and event["event"] != event_name:
            continue
        if request_id is None:
            return event
        try:
            parsed_data = json.loads(event["data"])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed_data, dict) and parsed_data.get("id") == request_id:
            event["parsed_json"] = parsed_data
            return event


async def send_sse_transaction(endpoint_url: str, payload: Any, protocol_version: str) -> dict[str, Any]:
    request_id = extract_request_id(payload)
    request_method = payload.get("method") if isinstance(payload, dict) else None
    needs_bootstrap = request_method not in {"initialize", "notifications/initialized"}
    async with httpx.AsyncClient(
        timeout=15.0,
        follow_redirects=True,
        verify=False,
    ) as client:
        async with client.stream(
            "GET",
            endpoint_url,
            headers={
                **DEFAULT_HEADERS,
                "Accept": SSE_ACCEPT_HEADER,
            },
        ) as stream_response:
            stream_response.raise_for_status()

            queue: asyncio.Queue = asyncio.Queue()
            reader_task = asyncio.create_task(read_sse_events(stream_response, queue))

            try:
                endpoint_event = await wait_for_sse_event(queue, event_name="endpoint")
                message_url = urljoin(str(stream_response.url), endpoint_event["data"])
                session_id = extract_sse_session_id(message_url)
                bootstrap_info: dict[str, Any] | None = None
                if needs_bootstrap:
                    initialize_payload = make_initialize_request(protocol_version)
                    initialize_response = await client.post(
                        message_url,
                        content=json.dumps(initialize_payload, ensure_ascii=False),
                        headers={
                            **DEFAULT_HEADERS,
                            "Accept": JSON_ACCEPT_HEADER,
                            "Content-Type": "application/json",
                            "Connection": "close",
                            "mcp-protocol-version": protocol_version,
                        },
                    )
                    initialize_http = parse_http_response(initialize_response)
                    session_id = session_id or initialize_http.get("mcp_session_id")
                    initialize_event = await wait_for_sse_event(
                        queue,
                        request_id=initialize_payload["id"],
                    )

                    initialized_response = await client.post(
                        message_url,
                        content=json.dumps(make_initialized_notification(), ensure_ascii=False),
                        headers={
                            **DEFAULT_HEADERS,
                            "Accept": JSON_ACCEPT_HEADER,
                            "Content-Type": "application/json",
                            "Connection": "close",
                            "mcp-protocol-version": protocol_version,
                        },
                    )
                    bootstrap_info = {
                        "initialize_http": initialize_http,
                        "initialize_event": to_jsonable(
                            initialize_event.get("parsed_json", initialize_event["data"])
                        ),
                        "initialized_http": parse_http_response(initialized_response),
                    }

                request_response = await post_with_retry(
                    client,
                    message_url,
                    content=json.dumps(payload, ensure_ascii=False),
                    headers={
                        **DEFAULT_HEADERS,
                        "Accept": JSON_ACCEPT_HEADER,
                        "Content-Type": "application/json",
                        "Connection": "close",
                        "mcp-protocol-version": protocol_version,
                    },
                )
                request_http = parse_http_response(request_response)
                session_id = session_id or request_http.get("mcp_session_id")

                matched_event: dict[str, Any] | None = None
                if request_id is not None:
                    matched_event = await wait_for_sse_event(queue, request_id=request_id)

                return {
                    "connection": {
                        "transport": "sse",
                        "endpoint_url": endpoint_url,
                        "message_url": message_url,
                        "protocol_version": protocol_version,
                        "mcp_session_id": session_id,
                    },
                    "bootstrap": bootstrap_info,
                    "response": {
                        "request_http": request_http,
                        "event": to_jsonable(
                            matched_event.get("parsed_json", matched_event["data"])
                            if matched_event
                            else None
                        ),
                    },
                }
            finally:
                reader_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await reader_task


async def send_mcp_transaction(endpoint_url: str, payload: Any, protocol_version: str) -> dict[str, Any]:
    async with httpx.AsyncClient(
        timeout=15.0,
        follow_redirects=True,
        verify=False,
    ) as client:
        request_method = payload.get("method") if isinstance(payload, dict) else None
        bootstrap_info: dict[str, Any] | None = None
        session_id: str | None = None

        if request_method != "initialize":
            initialize_payload = make_initialize_request(protocol_version)
            initialize_reply = await send_http_request(
                client,
                endpoint_url,
                initialize_payload,
                protocol_version,
            )
            session_id = initialize_reply.get("mcp_session_id")
            if not session_id:
                raise MCPGatewayError(
                    "The server did not return mcp-session-id during the initialize handshake."
                )

            initialized_reply = await send_http_request(
                client,
                endpoint_url,
                make_initialized_notification(),
                protocol_version,
                session_id=session_id,
            )
            bootstrap_info = {
                "initialize": initialize_reply,
                "initialized": initialized_reply,
            }

        request_reply = await send_http_request(
            client,
            endpoint_url,
            payload,
            protocol_version,
            session_id=session_id,
        )

        return {
            "connection": {
                "transport": "streamable-http",
                "endpoint_url": endpoint_url,
                "protocol_version": protocol_version,
                "mcp_session_id": session_id,
            },
            "bootstrap": bootstrap_info,
            "response": request_reply,
        }


async def connect_mcp_session(endpoint_url: str, protocol_version: str) -> dict[str, Any]:
    probe_payload = {
        "jsonrpc": "2.0",
        "id": "probe-tools-list",
        "method": "tools/list",
    }

    async with httpx.AsyncClient(
        timeout=15.0,
        follow_redirects=True,
        verify=False,
    ) as client:
        initialize_reply = await send_http_request(
            client,
            endpoint_url,
            make_initialize_request(protocol_version),
            protocol_version,
        )
        session_id = initialize_reply.get("mcp_session_id")
        if not session_id:
            raise MCPGatewayError(
                "The server did not return mcp-session-id during the initialize handshake."
            )

        initialized_reply = await send_http_request(
            client,
            endpoint_url,
            make_initialized_notification(),
            protocol_version,
            session_id=session_id,
        )
        request_reply = await send_http_request(
            client,
            endpoint_url,
            probe_payload,
            protocol_version,
            session_id=session_id,
        )

    return {
        "connection": {
            "transport": "streamable-http",
            "endpoint_url": endpoint_url,
            "protocol_version": protocol_version,
            "mcp_session_id": session_id,
        },
        "bootstrap": {
            "initialize": initialize_reply,
            "initialized": initialized_reply,
        },
        "response": request_reply,
    }


async def send_mcp_request_on_session(
    endpoint_url: str,
    payload: Any,
    session_id: str,
    protocol_version: str,
) -> dict[str, Any]:
    async with httpx.AsyncClient(
        timeout=15.0,
        follow_redirects=True,
        verify=False,
    ) as client:
        request_reply = await send_http_request(
            client,
            endpoint_url,
            payload,
            protocol_version,
            session_id=session_id,
        )

    return {
        "connection": {
            "transport": "streamable-http",
            "endpoint_url": endpoint_url,
            "protocol_version": protocol_version,
            "mcp_session_id": session_id,
        },
        "response": request_reply,
    }


async def disconnect_mcp_session(endpoint_url: str, session_id: str, protocol_version: str) -> dict[str, Any]:
    async with httpx.AsyncClient(
        timeout=15.0,
        follow_redirects=True,
        verify=False,
    ) as client:
        try:
            response = await delete_http_session(client, endpoint_url, session_id, protocol_version)
        except Exception as exc:
            return {
                "connection": {
                    "transport": "streamable-http",
                    "endpoint_url": endpoint_url,
                    "protocol_version": protocol_version,
                    "mcp_session_id": session_id,
                },
                "disconnected": True,
                "disconnect_error": f"{exc.__class__.__name__}: {exc}",
            }

    return {
        "connection": {
            "transport": "streamable-http",
            "endpoint_url": endpoint_url,
            "protocol_version": protocol_version,
            "mcp_session_id": session_id,
        },
        "response": response,
        "disconnected": True,
    }


async def connect_probe(
    target_url: str,
    transport: str,
    protocol_version: str = DEFAULT_PROTOCOL_VERSION,
) -> dict[str, Any]:
    endpoint_url = build_endpoint_url(target_url, transport)

    if normalize_transport(transport) == "sse":
        payload = {
            "jsonrpc": "2.0",
            "id": "probe-tools-list",
            "method": "tools/list",
        }
        result = await send_sse_transaction(endpoint_url, payload, protocol_version)
    else:
        result = await connect_mcp_session(endpoint_url, protocol_version)

    response_payload = result.get("response", {})
    http_result = response_payload.get("request_http", response_payload)
    if isinstance(http_result, dict) and http_result.get("status_code", 200) >= 400:
        raise MCPGatewayErrorWithPayload(
            "The MCP connection probe was blocked or rejected.",
            response_payload.get("event") or http_result.get("body") or http_result,
        )

    return {
        "state": "connected",
        "endpoint_url": endpoint_url,
        "transport": normalize_transport(transport),
        "probe": result,
    }


async def send_request(
    target_url: str,
    transport: str,
    payload: Any,
    protocol_version: str = DEFAULT_PROTOCOL_VERSION,
) -> dict[str, Any]:
    return await send_request_on_session(
        target_url,
        transport,
        payload,
        session_id=None,
        protocol_version=protocol_version,
    )


async def send_request_on_session(
    target_url: str,
    transport: str,
    payload: Any,
    session_id: str | None,
    protocol_version: str = DEFAULT_PROTOCOL_VERSION,
) -> dict[str, Any]:
    endpoint_url = build_endpoint_url(target_url, transport)
    normalized_transport = normalize_transport(transport)

    if normalized_transport == "sse":
        result = await send_sse_transaction(endpoint_url, payload, protocol_version)
    else:
        if session_id:
            result = await send_mcp_request_on_session(
                endpoint_url,
                payload,
                session_id,
                protocol_version,
            )
        else:
            result = await send_mcp_transaction(endpoint_url, payload, protocol_version)

    response_payload = result.get("response", {})
    http_result = response_payload.get("request_http", response_payload)
    if isinstance(http_result, dict) and http_result.get("status_code", 200) >= 400:
        raise MCPGatewayErrorWithPayload(
            "The MCP request was blocked or rejected.",
            response_payload.get("event") or http_result.get("body") or http_result,
        )
    return result


async def disconnect_session(
    target_url: str,
    transport: str,
    session_id: str | None,
    protocol_version: str = DEFAULT_PROTOCOL_VERSION,
) -> dict[str, Any]:
    endpoint_url = build_endpoint_url(target_url, transport)
    normalized_transport = normalize_transport(transport)

    if normalized_transport == "sse":
        return {
            "connection": {
                "transport": "sse",
                "endpoint_url": endpoint_url,
                "protocol_version": protocol_version,
            },
            "disconnected": True,
        }

    if not session_id:
        return {
            "connection": {
                "transport": "streamable-http",
                "endpoint_url": endpoint_url,
                "protocol_version": protocol_version,
            },
            "disconnected": True,
        }

    return await disconnect_mcp_session(endpoint_url, session_id, protocol_version)


class MCPGatewayErrorWithPayload(MCPGatewayError):
    """Raised when the server returns a readable error payload."""

    def __init__(self, message: str, payload: Any) -> None:
        super().__init__(message)
        self.payload = payload
