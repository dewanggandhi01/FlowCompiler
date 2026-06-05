"""
Repair Engine — Stage 5.

THE MOST IMPORTANT MODULE.

When validation fails, this engine performs TARGETED repairs.
It does NOT regenerate everything — only the failing section is repaired.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

from src.schemas.api_schema import APISchema
from src.schemas.auth_schema import AuthSchema
from src.schemas.db_schema import DBSchema
from src.schemas.ui_schema import UISchema
from src.schemas.validation_schema import (
    RepairReport,
    ValidationErrorDetail,
    ValidationLayer,
    ValidationResult,
)

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


# ── Repair-specific output models ────────────────────────


class UIRepairOutput(BaseModel):
    """Repaired UI schema."""
    ui: UISchema


class APIRepairOutput(BaseModel):
    """Repaired API schema."""
    api: APISchema


class DBRepairOutput(BaseModel):
    """Repaired DB schema."""
    db: DBSchema


class AuthRepairOutput(BaseModel):
    """Repaired Auth schema."""
    auth: AuthSchema


# ── Targeted Repair Agents ───────────────────────────────


class UIRepairAgent(BaseAgent):
    """Repairs UI schema based on validation errors."""

    @property
    def system_prompt(self) -> str:
        return """You are a UI schema repair specialist. You receive a UI schema with validation errors and must fix ONLY the errors listed. Do NOT change anything that isn't broken.

Rules:
1. Fix only the errors provided — do not restructure or redesign.
2. If a form references a missing endpoint, update the endpoint to match an existing one.
3. If a component references a missing form/table/chart, create the missing element.
4. Ensure all IDs are unique.
5. Ensure all routes start with '/'.
6. Preserve all existing valid data."""

    def build_user_prompt(self, input_data: Any) -> str:
        return f"""Fix the following UI schema errors.

## Current UI Schema:
{json.dumps(input_data['schema'], indent=2, default=str)}

## Validation Errors to Fix:
{json.dumps(input_data['errors'], indent=2, default=str)}

## Available API Endpoints (for reference):
{json.dumps(input_data.get('api_paths', []), indent=2)}

Fix ONLY the listed errors. Return the complete repaired UI schema."""

    @property
    def output_model(self) -> type[BaseModel]:
        return UIRepairOutput


class APIRepairAgent(BaseAgent):
    """Repairs API schema based on validation errors."""

    @property
    def system_prompt(self) -> str:
        return """You are an API schema repair specialist. You receive an API schema with validation errors and must fix ONLY the errors listed.

Rules:
1. Fix only the errors provided — do not restructure.
2. If an endpoint is missing, add it with proper CRUD conventions.
3. If a request/response model is missing, create it.
4. Ensure all IDs are unique.
5. Ensure all paths start with '/'.
6. Maintain RESTful conventions.
7. Preserve all existing valid data."""

    def build_user_prompt(self, input_data: Any) -> str:
        return f"""Fix the following API schema errors.

## Current API Schema:
{json.dumps(input_data['schema'], indent=2, default=str)}

## Validation Errors to Fix:
{json.dumps(input_data['errors'], indent=2, default=str)}

## Available DB Tables (for reference):
{json.dumps(input_data.get('db_tables', []), indent=2)}

Fix ONLY the listed errors. Return the complete repaired API schema."""

    @property
    def output_model(self) -> type[BaseModel]:
        return APIRepairOutput


class DBRepairAgent(BaseAgent):
    """Repairs DB schema based on validation errors."""

    @property
    def system_prompt(self) -> str:
        return """You are a database schema repair specialist. You receive a DB schema with validation errors and must fix ONLY the errors listed.

Rules:
1. Fix only the errors provided — do not restructure.
2. If a table is missing, add it with proper columns.
3. If a column is missing, add it to the correct table.
4. If a foreign key references a missing table/column, fix the reference.
5. Ensure every table has a primary key.
6. Ensure all foreign key references are valid.
7. Use snake_case for table and column names.
8. Preserve all existing valid data."""

    def build_user_prompt(self, input_data: Any) -> str:
        return f"""Fix the following DB schema errors.

## Current DB Schema:
{json.dumps(input_data['schema'], indent=2, default=str)}

## Validation Errors to Fix:
{json.dumps(input_data['errors'], indent=2, default=str)}

## Available Entities (from API, for reference):
{json.dumps(input_data.get('api_entities', []), indent=2)}

Fix ONLY the listed errors. Return the complete repaired DB schema."""

    @property
    def output_model(self) -> type[BaseModel]:
        return DBRepairOutput


class AuthRepairAgent(BaseAgent):
    """Repairs Auth schema based on validation errors."""

    @property
    def system_prompt(self) -> str:
        return """You are an authentication/authorization schema repair specialist. You receive an Auth schema with validation errors and must fix ONLY the errors listed.

Rules:
1. Fix only the errors provided — do not restructure.
2. If a role is missing, add it with reasonable permissions.
3. If a permission is missing, create it.
4. If RBAC rules reference invalid roles/permissions, fix the references.
5. Ensure at least one default role exists.
6. Preserve all existing valid data."""

    def build_user_prompt(self, input_data: Any) -> str:
        return f"""Fix the following Auth schema errors.

## Current Auth Schema:
{json.dumps(input_data['schema'], indent=2, default=str)}

## Validation Errors to Fix:
{json.dumps(input_data['errors'], indent=2, default=str)}

## Available Roles/Entities (for reference):
Roles used in UI/API: {json.dumps(input_data.get('referenced_roles', []), indent=2)}
Entities: {json.dumps(input_data.get('entities', []), indent=2)}

Fix ONLY the listed errors. Return the complete repaired Auth schema."""

    @property
    def output_model(self) -> type[BaseModel]:
        return AuthRepairOutput


# ── Main Repair Engine ───────────────────────────────────


class RepairEngine:
    """
    Stage 5: Repair Engine.

    Performs targeted repairs on failing schemas.
    Only repairs the specific layer(s) that have validation errors.
    """

    def __init__(self) -> None:
        self.ui_repair = UIRepairAgent()
        self.api_repair = APIRepairAgent()
        self.db_repair = DBRepairAgent()
        self.auth_repair = AuthRepairAgent()

    def repair(
        self,
        ui: UISchema,
        api: APISchema,
        db: DBSchema,
        auth: AuthSchema,
        validation_result: ValidationResult,
        iteration: int = 1,
    ) -> tuple[UISchema, APISchema, DBSchema, AuthSchema, RepairReport]:
        """
        Repair schemas based on validation errors.

        Only repairs layers that have errors — untouched layers are returned as-is.

        Returns:
            Tuple of (repaired_ui, repaired_api, repaired_db, repaired_auth, report)
        """
        errors = validation_result.errors
        if not errors:
            return ui, api, db, auth, RepairReport(
                iteration=iteration,
                layer=ValidationLayer.CROSS_LAYER,
                errors_fixed=[],
                errors_remaining=[],
                changes_made=["No errors to fix"],
                success=True,
            )

        # Categorize errors by layer
        ui_errors = [e for e in errors if e.layer in (ValidationLayer.UI, ValidationLayer.CROSS_LAYER) and "ui." in e.field]
        api_errors = [e for e in errors if e.layer in (ValidationLayer.API, ValidationLayer.CROSS_LAYER) and "api." in e.field]
        db_errors = [e for e in errors if e.layer in (ValidationLayer.DB, ValidationLayer.CROSS_LAYER) and "db." in e.field]
        auth_errors = [e for e in errors if e.layer in (ValidationLayer.AUTH, ValidationLayer.CROSS_LAYER) and "auth." in e.field]

        # Also catch cross-layer errors
        cross_errors = [e for e in errors if e.layer == ValidationLayer.CROSS_LAYER]
        for e in cross_errors:
            if "ui." in e.field and e not in ui_errors:
                ui_errors.append(e)
            elif "api." in e.field and e not in api_errors:
                api_errors.append(e)
            elif "db." in e.field and e not in db_errors:
                db_errors.append(e)
            elif "auth." in e.field and e not in auth_errors:
                auth_errors.append(e)

        # Catch uncategorized errors
        categorized = set(e.id for e in ui_errors + api_errors + db_errors + auth_errors)
        for e in errors:
            if e.id not in categorized:
                # Try to infer layer from error message
                msg_lower = e.message.lower()
                if "form" in msg_lower or "page" in msg_lower or "table" in msg_lower or "chart" in msg_lower:
                    ui_errors.append(e)
                elif "endpoint" in msg_lower or "request" in msg_lower or "response" in msg_lower:
                    api_errors.append(e)
                elif "column" in msg_lower or "foreign" in msg_lower or "primary" in msg_lower:
                    db_errors.append(e)
                elif "role" in msg_lower or "permission" in msg_lower or "rbac" in msg_lower:
                    auth_errors.append(e)

        changes_made = []
        errors_fixed = []
        repaired_ui = ui
        repaired_api = api
        repaired_db = db
        repaired_auth = auth

        # Repair each layer
        if ui_errors:
            repaired_ui, fixed = self._repair_ui(ui, ui_errors, api)
            changes_made.append(f"UI: Fixed {len(fixed)} errors")
            errors_fixed.extend(fixed)

        if api_errors:
            repaired_api, fixed = self._repair_api(api, api_errors, db)
            changes_made.append(f"API: Fixed {len(fixed)} errors")
            errors_fixed.extend(fixed)

        if db_errors:
            repaired_db, fixed = self._repair_db(db, db_errors, api)
            changes_made.append(f"DB: Fixed {len(fixed)} errors")
            errors_fixed.extend(fixed)

        if auth_errors:
            repaired_auth, fixed = self._repair_auth(
                auth, auth_errors, ui, api, db
            )
            changes_made.append(f"Auth: Fixed {len(fixed)} errors")
            errors_fixed.extend(fixed)

        all_error_ids = [e.id for e in errors]
        remaining = [eid for eid in all_error_ids if eid not in errors_fixed]

        report = RepairReport(
            iteration=iteration,
            layer=ValidationLayer.CROSS_LAYER,
            errors_fixed=errors_fixed,
            errors_remaining=remaining,
            changes_made=changes_made,
            success=len(remaining) == 0,
        )

        logger.info(
            f"Repair iteration {iteration}: "
            f"fixed {len(errors_fixed)}/{len(errors)} errors, "
            f"{len(remaining)} remaining"
        )

        return repaired_ui, repaired_api, repaired_db, repaired_auth, report

    def _repair_ui(
        self,
        ui: UISchema,
        errors: list[ValidationErrorDetail],
        api: APISchema,
    ) -> tuple[UISchema, list[str]]:
        """Repair UI schema."""
        try:
            api_paths = [ep.path for ep in api.endpoints + api.auth_endpoints]
            result = self.ui_repair.run({
                "schema": ui.model_dump(),
                "errors": [e.model_dump() for e in errors],
                "api_paths": api_paths,
            })
            return result.data.ui, [e.id for e in errors]
        except Exception as ex:
            logger.error(f"UI repair failed: {ex}")
            return ui, []

    def _repair_api(
        self,
        api: APISchema,
        errors: list[ValidationErrorDetail],
        db: DBSchema,
    ) -> tuple[APISchema, list[str]]:
        """Repair API schema."""
        try:
            db_tables = [t.name for t in db.tables]
            result = self.api_repair.run({
                "schema": api.model_dump(),
                "errors": [e.model_dump() for e in errors],
                "db_tables": db_tables,
            })
            return result.data.api, [e.id for e in errors]
        except Exception as ex:
            logger.error(f"API repair failed: {ex}")
            return api, []

    def _repair_db(
        self,
        db: DBSchema,
        errors: list[ValidationErrorDetail],
        api: APISchema,
    ) -> tuple[DBSchema, list[str]]:
        """Repair DB schema."""
        try:
            api_entities = list({ep.entity for ep in api.endpoints})
            result = self.db_repair.run({
                "schema": db.model_dump(),
                "errors": [e.model_dump() for e in errors],
                "api_entities": api_entities,
            })
            return result.data.db, [e.id for e in errors]
        except Exception as ex:
            logger.error(f"DB repair failed: {ex}")
            return db, []

    def _repair_auth(
        self,
        auth: AuthSchema,
        errors: list[ValidationErrorDetail],
        ui: UISchema,
        api: APISchema,
        db: DBSchema,
    ) -> tuple[AuthSchema, list[str]]:
        """Repair Auth schema."""
        try:
            # Collect all roles referenced across layers
            referenced_roles = set()
            for page in ui.pages:
                referenced_roles.update(page.allowed_roles)
            for ep in api.endpoints:
                referenced_roles.update(ep.allowed_roles)

            entities = list({ep.entity for ep in api.endpoints})

            result = self.auth_repair.run({
                "schema": auth.model_dump(),
                "errors": [e.model_dump() for e in errors],
                "referenced_roles": sorted(referenced_roles),
                "entities": entities,
            })
            return result.data.auth, [e.id for e in errors]
        except Exception as ex:
            logger.error(f"Auth repair failed: {ex}")
            return auth, []
