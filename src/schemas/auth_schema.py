"""
Auth Schema — Stage 3D output.

Defines the structured output for the Authentication & Authorization
portion of the Schema Generation Agent.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────


class AuthMethod(str, Enum):
    JWT = "jwt"
    SESSION = "session"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"


class PermissionAction(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    EXPORT = "export"
    IMPORT = "import"
    MANAGE = "manage"
    ALL = "*"


class AccessScope(str, Enum):
    ALL = "all"
    OWN = "own"
    TEAM = "team"
    DEPARTMENT = "department"


# ── Sub-models ───────────────────────────────────────────


class Permission(BaseModel):
    """A single permission definition."""
    id: str = Field(..., description="Permission slug, e.g. contacts:create")
    entity: str = Field(..., description="Entity this permission applies to")
    action: PermissionAction
    scope: AccessScope = Field(default=AccessScope.ALL)
    description: str = Field(default="")


class AuthRole(BaseModel):
    """A role with its assigned permissions."""
    name: str = Field(..., description="Role name")
    description: str = Field(default="")
    is_default: bool = Field(default=False)
    is_admin: bool = Field(default=False)
    permissions: list[str] = Field(
        default_factory=list,
        description="List of Permission IDs assigned to this role",
    )
    inherits_from: list[str] = Field(
        default_factory=list,
        description="Roles this role inherits permissions from",
    )


class RBACRule(BaseModel):
    """A specific RBAC rule mapping role to resource access."""
    id: str = Field(..., description="Rule identifier")
    role: str = Field(..., description="Role name")
    entity: str = Field(..., description="Entity name")
    action: PermissionAction
    scope: AccessScope = Field(default=AccessScope.ALL)
    conditions: list[str] = Field(
        default_factory=list,
        description="Additional conditions, e.g., 'status == active'",
    )
    ui_element: str = Field(
        default="",
        description="UI element to show/hide based on this rule",
    )
    api_endpoint: str = Field(
        default="",
        description="API endpoint this rule protects",
    )


class AuthConfig(BaseModel):
    """Authentication configuration."""
    method: AuthMethod = Field(default=AuthMethod.JWT)
    token_expiry_minutes: int = Field(default=60)
    refresh_token_enabled: bool = Field(default=True)
    refresh_token_expiry_days: int = Field(default=7)
    password_min_length: int = Field(default=8)
    password_require_uppercase: bool = Field(default=True)
    password_require_number: bool = Field(default=True)
    password_require_special: bool = Field(default=False)
    mfa_enabled: bool = Field(default=False)
    oauth_providers: list[str] = Field(default_factory=list, description="e.g., google, github")


class ProtectedRoute(BaseModel):
    """A UI route that requires authentication/authorization."""
    route: str
    requires_auth: bool = Field(default=True)
    allowed_roles: list[str] = Field(default_factory=list)
    redirect_on_unauthorized: str = Field(default="/login")


# ── Main Output ──────────────────────────────────────────


class AuthSchema(BaseModel):
    """
    Stage 3D Output: Complete authentication and authorization schema.

    Defines roles, permissions, RBAC rules, and auth configuration.
    """
    config: AuthConfig = Field(default_factory=AuthConfig)
    roles: list[AuthRole] = Field(default_factory=list)
    permissions: list[Permission] = Field(default_factory=list)
    rbac: list[RBACRule] = Field(default_factory=list)
    protected_routes: list[ProtectedRoute] = Field(default_factory=list)
