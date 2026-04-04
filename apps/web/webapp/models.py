from typing import Any, Literal

from pydantic import BaseModel, Field


TransportMode = Literal["sse", "mcp"]


class ConnectPayload(BaseModel):
    target_url: str = Field(..., min_length=1)
    transport: TransportMode


class SendRequestPayload(BaseModel):
    target_url: str = Field(..., min_length=1)
    transport: TransportMode
    request: Any
