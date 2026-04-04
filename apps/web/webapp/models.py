from typing import Any, Literal

from pydantic import BaseModel, Field


TransportMode = Literal["sse", "mcp"]


class ConnectPayload(BaseModel):
    target_url: str = Field(..., min_length=1)
    transport: TransportMode
    client_session_id: str = Field(..., min_length=1)


class SendRequestPayload(BaseModel):
    target_url: str = Field(..., min_length=1)
    transport: TransportMode
    client_session_id: str = Field(..., min_length=1)
    request: Any


class DisconnectPayload(BaseModel):
    client_session_id: str = Field(..., min_length=1)
