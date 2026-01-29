from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# ==================================================
# CHAT MESSAGE SCHEMA
# ==================================================

class Message(BaseModel):
    """
    Represents a single chat message.
    Compatible with OpenAI-style chat APIs.
    """
    role: str = Field(..., description="user | system | assistant")
    content: str = Field(..., description="Message content")


# ==================================================
# CHAT REQUEST SCHEMA
# ==================================================

class LLMRequest(BaseModel):
    """
    Incoming request to the LLM security proxy.
    """

    model: str = Field(
        ...,
        description="LLM model identifier (required, OpenAI-compatible)"
    )

    messages: List[Message] = Field(
        ...,
        description="Conversation messages"
    )

    stream: Optional[bool] = Field(
        default=False,
        description="Enable streaming (SSE)"
    )

    mode: Optional[str] = Field(
        default="enforce",
        description="Security mode: scan | enforce"
    )


# ==================================================
# CHAT RESPONSE SCHEMA
# ==================================================

class LLMResponse(BaseModel):
    """
    Final response returned by the proxy.
    """

    request_id: str = Field(
        ...,
        description="Unique request identifier"
    )

    content: str = Field(
        ...,
        description="Model response or block message"
    )

    blocked: bool = Field(
        ...,
        description="Whether the request was blocked"
    )

    violations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Detected security violations"
    )

    explanation: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Human-readable security explanation"
    )