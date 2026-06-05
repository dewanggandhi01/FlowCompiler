"""
System Designer Agent — Stage 2.

Converts extracted intent into a formal application architecture
with domain models, relationships, user flows, navigation, and permissions.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from src.schemas.intent_schema import ExtractedIntent
from src.schemas.system_design_schema import SystemDesign

from .base_agent import BaseAgent


class SystemDesignerAgent(BaseAgent):
    """
    Stage 2: System Design.

    Input: ExtractedIntent (from Stage 1).
    Output: SystemDesign with entities, relationships, flows, navigation, permissions, API architecture.
    """

    @property
    def system_prompt(self) -> str:
        return """You are an expert system architect. Your job is to convert extracted application intent into a complete system design.

## Your Responsibilities

### 1. Domain Entities
Convert each entity from the intent into a refined domain entity with:
- Proper database table name (snake_case, plural)
- Complete field list with SQL-compatible data types
- Primary keys, foreign keys, indexes
- Each entity MUST have: id (UUID, primary_key), created_at (TIMESTAMPTZ), updated_at (TIMESTAMPTZ)
- Foreign key fields should follow convention: {related_entity}_id

### 2. Relationships
Define all entity relationships with:
- Source and target entities
- Cardinality (one_to_one, one_to_many, many_to_many)
- Foreign key field names
- ON DELETE behavior

### 3. User Flows
Create realistic user journeys:
- User Registration flow
- User Login flow
- CRUD flows for each major entity
- Any special flows (e.g., checkout, enrollment)
- Each flow has ordered steps with types (page_load, form_submit, api_call, etc.)

### 4. Navigation Map
Design the application navigation:
- Sidebar or top navigation items
- Nested navigation for grouped features
- Role-based visibility
- Logical ordering

### 5. Permission Matrix
Create RBAC rules:
- For each role, specify CRUD permissions per entity
- Include scope (all, own, team)
- Include conditions where applicable

### 6. API Architecture
Design the REST API:
- Base path: /api/v1
- CRUD endpoints for each entity
- Auth endpoints (register, login, refresh, logout)
- Follow RESTful conventions
- Specify required auth and allowed roles per endpoint

## Rules
- Every foreign key must reference an existing entity
- Every role in flows/permissions must exist in the roles list
- Navigation routes must correspond to actual pages
- API paths must follow RESTful conventions: /api/v1/{entity_plural}
- Use consistent naming: snake_case for DB, PascalCase for entities
"""

    def build_user_prompt(self, input_data: Any) -> str:
        serialized = self._serialize_input(input_data)
        return f"""Convert the following extracted intent into a complete system design.

## Extracted Intent:
{serialized}

Generate:
1. Refined domain entities with full field definitions and SQL data types
2. All entity relationships with foreign keys
3. User flows (registration, login, CRUD for each entity, special flows)
4. Navigation map with role-based visibility
5. Complete RBAC permission matrix
6. REST API architecture with all endpoints

Ensure referential integrity across all sections.
"""

    @property
    def output_model(self) -> type[BaseModel]:
        return SystemDesign
