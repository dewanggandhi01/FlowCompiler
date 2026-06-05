"""
Intent Schema — Stage 1 output.

Defines the structured output for the Intent Extraction Agent.
Every field is strictly typed; no free-form text is returned.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────


class DomainType(str, Enum):
    """Recognized application domain types."""
    CRM = "crm"
    ERP = "erp"
    LMS = "lms"
    ECOMMERCE = "ecommerce"
    BOOKING = "booking"
    INVENTORY = "inventory"
    PROJECT_MANAGEMENT = "project_management"
    SOCIAL_MEDIA = "social_media"
    HEALTHCARE = "healthcare"
    REAL_ESTATE = "real_estate"
    FINANCE = "finance"
    ANALYTICS = "analytics"
    CUSTOM = "custom"


class FieldType(str, Enum):
    """Supported field/data types for entities."""
    STRING = "string"
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    URL = "url"
    PHONE = "phone"
    PASSWORD = "password"
    FILE = "file"
    IMAGE = "image"
    JSON = "json"
    UUID = "uuid"
    ENUM = "enum"
    MONEY = "money"


class RelationType(str, Enum):
    """Entity relationship types."""
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_MANY = "many_to_many"


# ── Sub-models ───────────────────────────────────────────


class EntityField(BaseModel):
    """A single field within an entity."""
    name: str = Field(..., description="Field name in snake_case")
    field_type: FieldType = Field(..., description="Data type")
    required: bool = Field(default=True)
    unique: bool = Field(default=False)
    default: Optional[str] = Field(default=None, description="Default value as string")
    enum_values: list[str] = Field(default_factory=list, description="Allowed values if type is ENUM")
    description: str = Field(default="", description="Human-readable description")


class Entity(BaseModel):
    """A domain entity (maps to a DB table and API resource)."""
    name: str = Field(..., description="Entity name in PascalCase")
    description: str = Field(default="")
    fields: list[EntityField] = Field(default_factory=list)
    is_user_entity: bool = Field(default=False, description="Whether this is the primary user entity")


class EntityRelationship(BaseModel):
    """Relationship between two entities."""
    source_entity: str = Field(..., description="Source entity name")
    target_entity: str = Field(..., description="Target entity name")
    relation_type: RelationType
    field_name: str = Field(..., description="FK field name on the source entity")
    description: str = Field(default="")


class Feature(BaseModel):
    """An application feature or capability."""
    name: str = Field(..., description="Feature name")
    description: str = Field(default="")
    entities_involved: list[str] = Field(default_factory=list)
    requires_auth: bool = Field(default=True)
    category: str = Field(default="core", description="Feature category: core, premium, admin")


class Role(BaseModel):
    """A user role for RBAC."""
    name: str = Field(..., description="Role name, e.g. admin, user, manager")
    description: str = Field(default="")
    is_default: bool = Field(default=False, description="Assigned to new users by default")
    permissions: list[str] = Field(default_factory=list, description="Permission slugs")


class PageComponent(BaseModel):
    """A component within a page."""
    type: str = Field(..., description="Component type: form, table, chart, card, list, detail")
    entity: str = Field(default="", description="Entity this component is bound to")
    description: str = Field(default="")


class Page(BaseModel):
    """A page/screen in the application."""
    name: str = Field(..., description="Page name")
    route: str = Field(..., description="URL path, e.g. /dashboard")
    description: str = Field(default="")
    components: list[PageComponent] = Field(default_factory=list)
    requires_auth: bool = Field(default=True)
    allowed_roles: list[str] = Field(default_factory=list, description="Roles that can access this page")


class Integration(BaseModel):
    """An external integration or service."""
    name: str = Field(..., description="Integration name, e.g. Stripe, SendGrid")
    type: str = Field(..., description="Type: payment, email, storage, analytics, notification")
    description: str = Field(default="")
    required: bool = Field(default=True)


class PaymentRequirement(BaseModel):
    """Payment and billing requirements."""
    has_payments: bool = Field(default=False)
    payment_provider: str = Field(default="stripe")
    has_subscriptions: bool = Field(default=False)
    plan_names: list[str] = Field(default_factory=list, description="e.g. free, basic, premium")
    has_invoicing: bool = Field(default=False)


class AnalyticsRequirement(BaseModel):
    """Analytics and reporting requirements."""
    has_analytics: bool = Field(default=False)
    dashboard_metrics: list[str] = Field(default_factory=list)
    report_types: list[str] = Field(default_factory=list)
    has_admin_analytics: bool = Field(default=False)


class Assumption(BaseModel):
    """An assumption made when input is ambiguous."""
    category: str = Field(..., description="What area the assumption covers")
    description: str = Field(..., description="The assumption made")
    reasoning: str = Field(default="", description="Why this assumption was made")


# ── Main Output ──────────────────────────────────────────


class ExtractedIntent(BaseModel):
    """
    Stage 1 Output: Complete extracted intent from natural language.

    This is the structured output of the Intent Extraction Agent.
    Every field is strictly typed — no free-form text.
    """
    app_name: str = Field(..., description="Application name derived from the prompt")
    domain: DomainType = Field(..., description="Primary application domain")
    description: str = Field(default="", description="One-line description of the application")
    entities: list[Entity] = Field(default_factory=list)
    relationships: list[EntityRelationship] = Field(default_factory=list)
    features: list[Feature] = Field(default_factory=list)
    roles: list[Role] = Field(default_factory=list)
    pages: list[Page] = Field(default_factory=list)
    integrations: list[Integration] = Field(default_factory=list)
    payment: PaymentRequirement = Field(default_factory=PaymentRequirement)
    analytics: AnalyticsRequirement = Field(default_factory=AnalyticsRequirement)
    assumptions: list[Assumption] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "app_name": "SmartCRM",
                    "domain": "crm",
                    "description": "A CRM with login, contacts, dashboard, RBAC, payments, and analytics",
                    "entities": [
                        {
                            "name": "User",
                            "description": "Application user",
                            "fields": [
                                {"name": "email", "field_type": "email", "required": True, "unique": True},
                                {"name": "password_hash", "field_type": "password", "required": True},
                                {"name": "full_name", "field_type": "string", "required": True},
                            ],
                            "is_user_entity": True,
                        }
                    ],
                    "roles": [
                        {"name": "admin", "description": "Full access", "permissions": ["*"]},
                        {"name": "user", "description": "Standard user", "is_default": True},
                    ],
                }
            ]
        }
    }
