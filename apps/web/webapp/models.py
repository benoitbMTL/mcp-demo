from typing import Any, Literal

from pydantic import BaseModel, Field


TransportMode = Literal["sse", "streamable-http"]
ProtocolVersion = Literal["2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05"]


class ConnectPayload(BaseModel):
    target_url: str = Field(..., min_length=1)
    transport: TransportMode
    protocol_version: ProtocolVersion
    client_session_id: str = Field(..., min_length=1)


class SendRequestPayload(BaseModel):
    target_url: str = Field(..., min_length=1)
    transport: TransportMode
    protocol_version: ProtocolVersion
    client_session_id: str = Field(..., min_length=1)
    request: Any


class DisconnectPayload(BaseModel):
    client_session_id: str = Field(..., min_length=1)
    protocol_version: ProtocolVersion


class ServerControlPayload(BaseModel):
    transport: TransportMode
    protocol_version: ProtocolVersion
    host: str = Field(..., min_length=1)
    port: int = Field(..., ge=1, le=65535)
