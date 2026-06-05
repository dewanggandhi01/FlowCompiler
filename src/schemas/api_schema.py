"""
API Schema — Stage 3B output.

Defines the structured output for the API portion of the Schema Generation Agent.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class FieldLocation(str, Enum):
    BODY = "body"
    QUERY = "query"
    PATH = "path"
    HEADER = "header"


class ResponseType(str, Enum):
    SINGLE = "single"
    LIST = "list"
    PAGINATED = "paginated"
    MESSAGE = "message"
    TOKEN = "token"
    FILE = "file"
    EMPTY = "empty"


# ── Sub-models ───────────────────────────────────────────


class RequestField(BaseModel):
    """A field in an API request model."""
    name: str = Field(..., description="Field name")
    field_type: str = Field(..., description="Data type: string, integer, float, boolean, date, email, etc.")
    required: bool = Field(default=True)
    location: FieldLocation = Field(default=FieldLocation.BODY)
    description: str = Field(default="")
    default: Optional[str] = None
    enum_values: list[str] = Field(default_factory=list)
    validation: dict = Field(
        default_factory=dict,
        description="Validation rules: min_length, max_length, pattern, etc.",
    )


class ResponseField(BaseModel):
    """A field in an API response model."""
    name: str = Field(..., description="Field name")
    field_type: str = Field(..., description="Data type")
    description: str = Field(default="")
    nullable: bool = Field(default=False)


class RequestModel(BaseModel):
    """An API request body model."""
    id: str = Field(..., description="Unique model identifier")
    name: str = Field(..., description="Model name, e.g. CreateContactRequest")
    entity: str = Field(..., description="Entity this model is for")
    fields: list[RequestField] = Field(default_factory=list)
    description: str = Field(default="")


class ResponseModel(BaseModel):
    """An API response body model."""
    id: str = Field(..., description="Unique model identifier")
    name: str = Field(..., description="Model name, e.g. ContactResponse")
    entity: str = Field(..., description="Entity this model is for")
    response_type: ResponseType = Field(default=ResponseType.SINGLE)
    fields: list[ResponseField] = Field(default_factory=list)
    description: str = Field(default="")


class ErrorResponse(BaseModel):
    """Standard API error response."""
    status_code: int
    error_code: str
    message: str


class APIEndpoint(BaseModel):
    """A single API endpoint definition."""
    id: str = Field(..., description="Unique endpoint identifier")
    path: str = Field(..., description="Full API path, e.g. /api/v1/contacts")
    method: HTTPMethod
    entity: str = Field(..., description="Primary entity this endpoint operates on")
    operation: str = Field(..., description="Operation: create, read, update, delete, list, search, custom")
    description: str = Field(default="")
    summary: str = Field(default="", description="Short summary for API docs")
    tags: list[str] = Field(default_factory=list, description="API documentation tags")

    # Auth
    requires_auth: bool = Field(default=True)
    allowed_roles: list[str] = Field(default_factory=list)

    # Request
    request_model_id: Optional[str] = Field(default=None, description="Reference to RequestModel.id")
    path_params: list[str] = Field(default_factory=list, description="Path parameter names")
    query_params: list[RequestField] = Field(default_factory=list)

    # Response
    response_model_id: Optional[str] = Field(default=None, description="Reference to ResponseModel.id")
    success_status: int = Field(default=200)
    error_responses: list[ErrorResponse] = Field(default_factory=list)

    # Rate limiting
    rate_limit: Optional[str] = Field(default=None, description="Rate limit, e.g. '100/minute'")


class MiddlewareConfig(BaseModel):
    """API middleware configuration."""
    name: str
    enabled: bool = Field(default=True)
    config: dict = Field(default_factory=dict)


# ── Main Output ──────────────────────────────────────────


class APISchema(BaseModel):
    """
    Stage 3B Output: Complete API schema.

    Defines all endpoints, request/response models, and middleware.
    """
    base_path: str = Field(default="/api/v1")
    title: str = Field(default="FlowCompiler Generated API")
    version: str = Field(default="1.0.0")
    description: str = Field(default="")

    endpoints: list[APIEndpoint] = Field(default_factory=list)
    request_models: list[RequestModel] = Field(default_factory=list)
    response_models: list[ResponseModel] = Field(default_factory=list)

    middleware: list[MiddlewareConfig] = Field(
        default_factory=lambda: [
            MiddlewareConfig(name="cors", config={"origins": ["*"]}),
            MiddlewareConfig(name="rate_limiter", config={"default": "100/minute"}),
            MiddlewareConfig(name="auth", config={"type": "jwt"}),
        ]
    )

    auth_endpoints: list[APIEndpoint] = Field(
        default_factory=list,
        description="Authentication-specific endpoints (login, register, etc.)",
    )
