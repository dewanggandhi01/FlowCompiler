"""
System Design Schema — Stage 2 output.

Defines the structured output for the System Design Agent.
Converts extracted intent into a formal application architecture.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────


class CardinalityType(str, Enum):
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_MANY = "many_to_many"


class FlowStepType(str, Enum):
    PAGE_LOAD = "page_load"
    FORM_SUBMIT = "form_submit"
    API_CALL = "api_call"
    NAVIGATION = "navigation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION_CHECK = "authorization_check"
    DATA_DISPLAY = "data_display"
    NOTIFICATION = "notification"
    PAYMENT = "payment"
    REDIRECT = "redirect"


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class CRUDOperation(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"


# ── Sub-models ───────────────────────────────────────────


class DomainField(BaseModel):
    """A field in a domain entity."""
    name: str
    data_type: str = Field(..., description="SQL-compatible data type")
    nullable: bool = Field(default=False)
    primary_key: bool = Field(default=False)
    unique: bool = Field(default=False)
    default: Optional[str] = None
    foreign_key: Optional[str] = Field(default=None, description="Reference in format 'table.column'")
    indexed: bool = Field(default=False)


class DomainEntity(BaseModel):
    """A refined domain entity with full metadata."""
    name: str = Field(..., description="Entity name in PascalCase")
    table_name: str = Field(..., description="Database table name in snake_case")
    description: str = Field(default="")
    is_core: bool = Field(default=True, description="Whether this is a core entity")
    fields: list[DomainField] = Field(default_factory=list)


class Relationship(BaseModel):
    """A relationship between two domain entities."""
    name: str = Field(..., description="Relationship name")
    source: str = Field(..., description="Source entity name")
    target: str = Field(..., description="Target entity name")
    cardinality: CardinalityType
    source_field: str = Field(..., description="FK field on source")
    target_field: str = Field(default="id", description="Referenced field on target")
    on_delete: str = Field(default="CASCADE")
    description: str = Field(default="")


class FlowStep(BaseModel):
    """A single step in a user flow."""
    order: int = Field(..., ge=1)
    step_type: FlowStepType
    description: str
    page: Optional[str] = Field(default=None, description="Page where this step occurs")
    endpoint: Optional[str] = Field(default=None, description="API endpoint involved")
    entity: Optional[str] = Field(default=None, description="Entity involved")
    requires_role: list[str] = Field(default_factory=list)


class UserFlow(BaseModel):
    """A complete user journey through the application."""
    name: str = Field(..., description="Flow name, e.g. 'User Registration'")
    description: str = Field(default="")
    actor_role: str = Field(..., description="Role performing this flow")
    steps: list[FlowStep] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)


class NavigationItem(BaseModel):
    """A navigation menu item."""
    label: str
    route: str
    icon: str = Field(default="")
    parent: Optional[str] = Field(default=None, description="Parent menu item for nested nav")
    allowed_roles: list[str] = Field(default_factory=list)
    order: int = Field(default=0)


class NavigationMap(BaseModel):
    """Complete navigation structure."""
    items: list[NavigationItem] = Field(default_factory=list)


class PermissionRule(BaseModel):
    """A single permission rule in the matrix."""
    role: str
    entity: str
    operations: list[CRUDOperation] = Field(default_factory=list)
    conditions: list[str] = Field(
        default_factory=list,
        description="Additional conditions, e.g. 'own_records_only'",
    )


class PermissionMatrix(BaseModel):
    """Complete RBAC permission matrix."""
    rules: list[PermissionRule] = Field(default_factory=list)


class APIRouteDesign(BaseModel):
    """Designed API route."""
    path: str = Field(..., description="API path, e.g. /api/contacts")
    method: HTTPMethod
    entity: str = Field(..., description="Entity this route operates on")
    operation: CRUDOperation
    description: str = Field(default="")
    requires_auth: bool = Field(default=True)
    allowed_roles: list[str] = Field(default_factory=list)
    request_body_fields: list[str] = Field(default_factory=list)
    response_fields: list[str] = Field(default_factory=list)


class APIArchitecture(BaseModel):
    """Complete API design."""
    base_path: str = Field(default="/api/v1")
    routes: list[APIRouteDesign] = Field(default_factory=list)


# ── Main Output ──────────────────────────────────────────


class SystemDesign(BaseModel):
    """
    Stage 2 Output: Complete system design derived from extracted intent.

    This is the structured output of the System Design Agent.
    """
    entities: list[DomainEntity] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    flows: list[UserFlow] = Field(default_factory=list)
    navigation: NavigationMap = Field(default_factory=NavigationMap)
    permissions: PermissionMatrix = Field(default_factory=PermissionMatrix)
    api_architecture: APIArchitecture = Field(default_factory=APIArchitecture)
    roles: list[str] = Field(default_factory=list, description="Flat list of role names")
