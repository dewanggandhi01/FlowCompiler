"""
Schema Generator Agent — Stage 3.

Generates all four schemas (UI, API, DB, Auth) from the system design.
This is the most complex agent — it produces the bulk of the executable configuration.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from src.schemas.api_schema import APISchema
from src.schemas.auth_schema import AuthSchema
from src.schemas.db_schema import DBSchema
from src.schemas.system_design_schema import SystemDesign
from src.schemas.ui_schema import UISchema

from .base_agent import BaseAgent


# ── Combined output model for structured generation ──────


class GeneratedSchemas(BaseModel):
    """Combined output of all four schema layers."""
    ui: UISchema = Field(default_factory=UISchema)
    api: APISchema = Field(default_factory=APISchema)
    db: DBSchema = Field(default_factory=DBSchema)
    auth: AuthSchema = Field(default_factory=AuthSchema)


class SchemaGeneratorAgent(BaseAgent):
    """
    Stage 3: Schema Generation.

    Input: SystemDesign (from Stage 2).
    Output: GeneratedSchemas containing UI, API, DB, and Auth schemas.
    """

    @property
    def system_prompt(self) -> str:
        return """You are an expert full-stack architect generating production-ready application schemas.
You must generate FOUR interconnected schemas that maintain referential integrity.

## A. UI Schema
For each page in the system design, generate:
- UIPage with unique ID, route, title, layout, components, auth requirements
- UIForm for every create/edit operation:
  - Fields matching entity fields with proper input types
  - Client-side validation rules (required, min_length, email format, etc.)
  - Submit endpoint matching an API endpoint
- UITable for every list view:
  - Columns matching entity fields
  - Actions (view, edit, delete)
  - Data endpoint matching an API endpoint
  - Pagination, sorting, filtering
- UIChart for dashboard metrics:
  - Appropriate chart types
  - Data source endpoints

### UI Component Naming Convention:
- Form IDs: form_{entity}_{action} (e.g., form_contact_create)
- Table IDs: table_{entity}_list (e.g., table_contact_list)
- Chart IDs: chart_{metric_name} (e.g., chart_revenue_monthly)
- Page IDs: page_{name} (e.g., page_dashboard)

## B. API Schema
For each entity, generate CRUD endpoints:
- GET /api/v1/{entities} - List all (paginated)
- GET /api/v1/{entities}/{id} - Get one
- POST /api/v1/{entities} - Create
- PUT /api/v1/{entities}/{id} - Update
- DELETE /api/v1/{entities}/{id} - Delete

Also generate:
- Auth endpoints: POST /api/v1/auth/register, /login, /refresh, /logout, /me
- Request models for create/update operations
- Response models for single and list responses
- Proper HTTP status codes and error responses
- Role-based access control on endpoints

### API Naming Convention:
- Endpoint IDs: {method}_{entity}_{operation} (e.g., post_contacts_create)
- Request model IDs: req_{entity}_{operation} (e.g., req_contact_create)
- Response model IDs: res_{entity}_{operation} (e.g., res_contact_single)

## C. DB Schema
For each entity, generate a table with:
- All columns with proper SQL types (UUID, VARCHAR, TEXT, INTEGER, etc.)
- Primary key (id UUID DEFAULT uuid_generate_v4())
- Foreign keys matching relationships
- Timestamps (created_at, updated_at)
- Proper constraints (NOT NULL, UNIQUE, CHECK)
- Indexes on foreign keys and frequently queried columns
- ENUM types where needed

### DB Naming Convention:
- Table names: snake_case, plural (e.g., contacts, deal_stages)
- Column names: snake_case (e.g., full_name, company_id)
- FK convention: {referenced_table_singular}_id
- Index names: idx_{table}_{column}

## D. Auth Schema
Generate:
- JWT authentication config
- Roles matching the system design roles
- Permissions for each entity CRUD operation
- RBAC rules linking roles to entity permissions
- Protected routes matching UI pages

### Auth Naming Convention:
- Permission IDs: {entity}:{action} (e.g., contacts:create)
- RBAC rule IDs: rbac_{role}_{entity}_{action}

## CRITICAL RULES
1. Every UI form submit_endpoint MUST match an existing API endpoint path
2. Every UI table data_endpoint MUST match an existing API endpoint path
3. Every API endpoint entity MUST have a corresponding DB table
4. Every API request model field MUST exist as a DB column
5. Every role in auth MUST be referenced consistently across all schemas
6. Every foreign key in DB MUST reference an existing table
7. No orphaned references — everything must connect
"""

    def build_user_prompt(self, input_data: Any) -> str:
        serialized = self._serialize_input(input_data)
        return f"""Generate all four schemas (UI, API, DB, Auth) from the following system design.

## System Design:
{serialized}

Generate complete, production-ready schemas with:
- UI: All pages, forms, tables, and charts
- API: All CRUD endpoints, auth endpoints, request/response models
- DB: All tables, columns, constraints, indexes, enums
- Auth: JWT config, roles, permissions, RBAC rules, protected routes

Ensure COMPLETE referential integrity across all four schemas.
Every UI element must connect to an API endpoint.
Every API endpoint must connect to a DB table.
Every protected resource must have auth rules.
"""

    @property
    def output_model(self) -> type[BaseModel]:
        return GeneratedSchemas
