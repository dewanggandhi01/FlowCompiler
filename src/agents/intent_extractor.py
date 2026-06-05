"""
Intent Extractor Agent — Stage 1.

Extracts structured intent from natural language software requirements.
Uses OpenAI structured outputs for deterministic, schema-constrained generation.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from src.schemas.intent_schema import ExtractedIntent

from .base_agent import BaseAgent


class IntentExtractorAgent(BaseAgent):
    """
    Stage 1: Intent Extraction.

    Input: Natural language prompt (string).
    Output: ExtractedIntent with entities, features, roles, pages, integrations.
    """

    @property
    def system_prompt(self) -> str:
        return """You are an expert software architect and requirements analyst.
Your job is to extract structured application requirements from natural language descriptions.

## Your Responsibilities
1. **Extract Entities**: Identify all domain entities (data models) with their fields and types.
   - Always include a User entity with email, password_hash, full_name, role fields.
   - Infer entities from the domain (e.g., CRM → Contact, Deal, Company; LMS → Course, Lesson, Enrollment).
   - Each entity must have an 'id' field (UUID type) and standard fields.

2. **Extract Entity Relationships**: Identify how entities relate to each other.
   - Specify source, target, relationship type (one_to_one, one_to_many, many_to_many).
   - Include the foreign key field name.

3. **Extract Features**: List all application features/capabilities.
   - Categorize as 'core', 'premium', or 'admin'.
   - Link features to the entities they involve.

4. **Extract Roles**: Identify user roles for RBAC.
   - Always include at least 'admin' and 'user' roles.
   - Mark one role as default (assigned to new users).
   - List permissions for each role.

5. **Extract Pages**: Identify all UI pages/screens.
   - Include route paths (e.g., /dashboard, /contacts).
   - Specify which components each page contains (form, table, chart, etc.).
   - Specify which roles can access each page.

6. **Extract Integrations**: Identify external service integrations.
   - Common: Stripe (payments), SendGrid (email), S3 (storage).

7. **Extract Payment Requirements**: If payments/billing are mentioned.
   - Subscription plans, invoicing, payment providers.

8. **Extract Analytics Requirements**: If analytics/reporting are mentioned.
   - Dashboard metrics, report types, admin analytics.

## Rules
- NEVER return free-form text. Only return structured data.
- If the prompt is ambiguous, make reasonable assumptions and document them.
- If the prompt is too vague (e.g., "build something for my business"), still produce a reasonable output with assumptions.
- Use snake_case for field names, PascalCase for entity names.
- Every entity should have: id (UUID), created_at (datetime), updated_at (datetime).
- Infer reasonable defaults when not specified.

## Common Domain Patterns
- CRM: User, Contact, Company, Deal, Task, Note, Activity
- ERP: User, Employee, Department, Product, Order, Invoice, Vendor
- LMS: User, Course, Lesson, Module, Enrollment, Quiz, Certificate
- E-commerce: User, Product, Category, Cart, Order, OrderItem, Review, Payment
- Booking: User, Service, Provider, Booking, TimeSlot, Review
- Inventory: User, Product, Warehouse, StockItem, Supplier, PurchaseOrder
"""

    def build_user_prompt(self, input_data: Any) -> str:
        prompt = input_data if isinstance(input_data, str) else str(input_data)
        return f"""Analyze the following software requirement and extract the complete structured intent.

## User's Requirement:
{prompt}

Extract ALL entities, features, roles, pages, integrations, payment requirements, and analytics requirements.
If information is missing or ambiguous, make reasonable assumptions and include them in the assumptions list.
Ensure every entity has proper fields with correct types.
Ensure relationships between entities are captured.
"""

    @property
    def output_model(self) -> type[BaseModel]:
        return ExtractedIntent
