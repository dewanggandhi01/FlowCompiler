"""
Validation Engine — Stage 4.

Pure Python validation (no AI calls needed).
Performs comprehensive cross-layer validation across UI, API, DB, and Auth schemas.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from src.schemas.api_schema import APISchema
from src.schemas.auth_schema import AuthSchema
from src.schemas.db_schema import DBSchema
from src.schemas.ui_schema import UISchema
from src.schemas.validation_schema import (
    ValidationErrorDetail,
    ValidationLayer,
    ValidationResult,
    ValidationSeverity,
)

logger = logging.getLogger(__name__)


class ValidationEngine:
    """
    Stage 4: Validation Engine.

    Performs five levels of validation:
    1. JSON/Schema Validation (handled by Pydantic)
    2. Type Validation
    3. Referential Integrity
    4. Cross-Layer Validation
    5. Completeness Checks

    This is a pure Python module — no AI calls.
    """

    def __init__(self) -> None:
        self.errors: list[ValidationErrorDetail] = []
        self.warnings: list[ValidationErrorDetail] = []
        self.total_checks = 0
        self.passed_checks = 0

    def validate(
        self,
        ui: UISchema,
        api: APISchema,
        db: DBSchema,
        auth: AuthSchema,
    ) -> ValidationResult:
        """
        Run all validation checks across all four schema layers.

        Returns a ValidationResult with status PASS or FAIL.
        """
        self.errors = []
        self.warnings = []
        self.total_checks = 0
        self.passed_checks = 0

        # Layer-specific validation
        self._validate_ui(ui)
        self._validate_api(api)
        self._validate_db(db)
        self._validate_auth(auth)

        # Cross-layer validation
        self._validate_ui_api(ui, api)
        self._validate_api_db(api, db)
        self._validate_auth_cross(auth, ui, api, db)
        self._validate_ui_db(ui, db)

        failed = len(self.errors)
        status = "PASS" if failed == 0 else "FAIL"

        result = ValidationResult(
            status=status,
            errors=self.errors,
            warnings=self.warnings,
            total_checks=self.total_checks,
            passed_checks=self.passed_checks,
            failed_checks=failed,
        )

        logger.info(
            f"Validation {status}: {self.passed_checks}/{self.total_checks} checks passed, "
            f"{failed} errors, {len(self.warnings)} warnings"
        )

        return result

    # ── Helper Methods ───────────────────────────────────

    def _add_error(
        self,
        layer: ValidationLayer,
        field: str,
        message: str,
        expected: str = "",
        actual: str = "",
        fix_suggestion: str = "",
        auto_fixable: bool = False,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        error = ValidationErrorDetail(
            id=f"err_{uuid.uuid4().hex[:8]}",
            layer=layer,
            severity=severity,
            field=field,
            message=message,
            expected=expected,
            actual=actual,
            fix_suggestion=fix_suggestion,
            auto_fixable=auto_fixable,
        )
        if severity == ValidationSeverity.ERROR:
            self.errors.append(error)
        else:
            self.warnings.append(error)

    def _check(self, passed: bool) -> bool:
        self.total_checks += 1
        if passed:
            self.passed_checks += 1
        return passed

    # ── UI Validation ────────────────────────────────────

    def _validate_ui(self, ui: UISchema) -> None:
        """Validate UI schema internal consistency."""
        page_ids = set()
        form_ids = {f.id for f in ui.forms}
        table_ids = {t.id for t in ui.tables}
        chart_ids = {c.id for c in ui.charts}

        # Check page uniqueness
        for page in ui.pages:
            if not self._check(page.id not in page_ids):
                self._add_error(
                    ValidationLayer.UI,
                    f"pages[{page.id}].id",
                    f"Duplicate page ID: {page.id}",
                    auto_fixable=True,
                )
            page_ids.add(page.id)

            # Check route format
            if not self._check(page.route.startswith("/")):
                self._add_error(
                    ValidationLayer.UI,
                    f"pages[{page.id}].route",
                    f"Route must start with '/': {page.route}",
                    expected="/some-path",
                    actual=page.route,
                    auto_fixable=True,
                )

            # Check component references
            for comp in page.components:
                if comp.ref_form:
                    if not self._check(comp.ref_form in form_ids):
                        self._add_error(
                            ValidationLayer.UI,
                            f"pages[{page.id}].components[{comp.id}].ref_form",
                            f"Form reference '{comp.ref_form}' not found in forms",
                            fix_suggestion=f"Add form with ID '{comp.ref_form}' to forms list",
                            auto_fixable=True,
                        )
                if comp.ref_table:
                    if not self._check(comp.ref_table in table_ids):
                        self._add_error(
                            ValidationLayer.UI,
                            f"pages[{page.id}].components[{comp.id}].ref_table",
                            f"Table reference '{comp.ref_table}' not found in tables",
                            fix_suggestion=f"Add table with ID '{comp.ref_table}' to tables list",
                            auto_fixable=True,
                        )
                if comp.ref_chart:
                    if not self._check(comp.ref_chart in chart_ids):
                        self._add_error(
                            ValidationLayer.UI,
                            f"pages[{page.id}].components[{comp.id}].ref_chart",
                            f"Chart reference '{comp.ref_chart}' not found in charts",
                            fix_suggestion=f"Add chart with ID '{comp.ref_chart}' to charts list",
                            auto_fixable=True,
                        )

        # Check forms have fields
        for form in ui.forms:
            if not self._check(len(form.fields) > 0):
                self._add_error(
                    ValidationLayer.UI,
                    f"forms[{form.id}].fields",
                    f"Form '{form.id}' has no fields",
                    auto_fixable=True,
                )

        # Check tables have columns
        for table in ui.tables:
            if not self._check(len(table.columns) > 0):
                self._add_error(
                    ValidationLayer.UI,
                    f"tables[{table.id}].columns",
                    f"Table '{table.id}' has no columns",
                    auto_fixable=True,
                )

    # ── API Validation ───────────────────────────────────

    def _validate_api(self, api: APISchema) -> None:
        """Validate API schema internal consistency."""
        endpoint_ids = set()
        request_model_ids = {m.id for m in api.request_models}
        response_model_ids = {m.id for m in api.response_models}

        for ep in api.endpoints:
            # Unique endpoint IDs
            if not self._check(ep.id not in endpoint_ids):
                self._add_error(
                    ValidationLayer.API,
                    f"endpoints[{ep.id}].id",
                    f"Duplicate endpoint ID: {ep.id}",
                    auto_fixable=True,
                )
            endpoint_ids.add(ep.id)

            # Path format
            if not self._check(ep.path.startswith("/")):
                self._add_error(
                    ValidationLayer.API,
                    f"endpoints[{ep.id}].path",
                    f"Endpoint path must start with '/': {ep.path}",
                    auto_fixable=True,
                )

            # Request model reference
            if ep.request_model_id:
                if not self._check(ep.request_model_id in request_model_ids):
                    self._add_error(
                        ValidationLayer.API,
                        f"endpoints[{ep.id}].request_model_id",
                        f"Request model '{ep.request_model_id}' not found",
                        auto_fixable=True,
                    )

            # Response model reference
            if ep.response_model_id:
                if not self._check(ep.response_model_id in response_model_ids):
                    self._add_error(
                        ValidationLayer.API,
                        f"endpoints[{ep.id}].response_model_id",
                        f"Response model '{ep.response_model_id}' not found",
                        auto_fixable=True,
                    )

        # Check for auth endpoints
        all_endpoints = api.endpoints + api.auth_endpoints
        auth_paths = [ep.path for ep in all_endpoints]
        has_login = any("/login" in p or "/auth/login" in p for p in auth_paths)
        has_register = any("/register" in p or "/auth/register" in p for p in auth_paths)

        if not self._check(has_login):
            self._add_error(
                ValidationLayer.API,
                "auth_endpoints",
                "Missing login endpoint",
                fix_suggestion="Add POST /api/v1/auth/login endpoint",
                auto_fixable=True,
            )
        if not self._check(has_register):
            self._add_error(
                ValidationLayer.API,
                "auth_endpoints",
                "Missing register endpoint",
                fix_suggestion="Add POST /api/v1/auth/register endpoint",
                auto_fixable=True,
            )

    # ── DB Validation ────────────────────────────────────

    def _validate_db(self, db: DBSchema) -> None:
        """Validate DB schema internal consistency."""
        table_names = set()
        table_column_map: dict[str, set[str]] = {}

        for table in db.tables:
            # Unique table names
            if not self._check(table.name not in table_names):
                self._add_error(
                    ValidationLayer.DB,
                    f"tables[{table.name}].name",
                    f"Duplicate table name: {table.name}",
                    auto_fixable=True,
                )
            table_names.add(table.name)
            table_column_map[table.name] = {col.name for col in table.columns}

            # Must have primary key
            has_pk = any(col.primary_key for col in table.columns)
            if not self._check(has_pk):
                self._add_error(
                    ValidationLayer.DB,
                    f"tables[{table.name}].columns",
                    f"Table '{table.name}' has no primary key",
                    fix_suggestion="Add 'id' column with primary_key=True",
                    auto_fixable=True,
                )

            # Check columns have names
            col_names = set()
            for col in table.columns:
                if not self._check(col.name not in col_names):
                    self._add_error(
                        ValidationLayer.DB,
                        f"tables[{table.name}].columns[{col.name}]",
                        f"Duplicate column name in table '{table.name}': {col.name}",
                        auto_fixable=True,
                    )
                col_names.add(col.name)

        # Validate foreign keys
        for table in db.tables:
            for fk in table.foreign_keys:
                # FK references existing table
                if not self._check(fk.references_table in table_names):
                    self._add_error(
                        ValidationLayer.DB,
                        f"tables[{table.name}].foreign_keys[{fk.column}]",
                        f"Foreign key references non-existent table: {fk.references_table}",
                        expected=f"One of: {', '.join(sorted(table_names))}",
                        actual=fk.references_table,
                        auto_fixable=True,
                    )
                else:
                    # FK references existing column
                    ref_cols = table_column_map.get(fk.references_table, set())
                    if not self._check(fk.references_column in ref_cols):
                        self._add_error(
                            ValidationLayer.DB,
                            f"tables[{table.name}].foreign_keys[{fk.column}]",
                            f"FK references non-existent column '{fk.references_column}' in table '{fk.references_table}'",
                            auto_fixable=True,
                        )

                # FK column exists in this table
                own_cols = table_column_map.get(table.name, set())
                if not self._check(fk.column in own_cols):
                    self._add_error(
                        ValidationLayer.DB,
                        f"tables[{table.name}].foreign_keys[{fk.column}]",
                        f"FK column '{fk.column}' does not exist in table '{table.name}'",
                        fix_suggestion=f"Add column '{fk.column}' to table '{table.name}'",
                        auto_fixable=True,
                    )

    # ── Auth Validation ──────────────────────────────────

    def _validate_auth(self, auth: AuthSchema) -> None:
        """Validate Auth schema internal consistency."""
        role_names = {r.name for r in auth.roles}
        permission_ids = {p.id for p in auth.permissions}

        # Must have at least one role
        if not self._check(len(auth.roles) > 0):
            self._add_error(
                ValidationLayer.AUTH,
                "roles",
                "No roles defined",
                fix_suggestion="Add at least 'admin' and 'user' roles",
                auto_fixable=True,
            )

        # Must have a default role
        has_default = any(r.is_default for r in auth.roles)
        if not self._check(has_default):
            self._add_error(
                ValidationLayer.AUTH,
                "roles",
                "No default role defined",
                fix_suggestion="Set is_default=True on one role",
                auto_fixable=True,
                severity=ValidationSeverity.WARNING,
            )

        # Check role permission references
        for role in auth.roles:
            for perm_id in role.permissions:
                if perm_id != "*":
                    if not self._check(perm_id in permission_ids):
                        self._add_error(
                            ValidationLayer.AUTH,
                            f"roles[{role.name}].permissions",
                            f"Permission '{perm_id}' referenced by role '{role.name}' does not exist",
                            auto_fixable=True,
                        )

            # Check inherits_from references
            for parent in role.inherits_from:
                if not self._check(parent in role_names):
                    self._add_error(
                        ValidationLayer.AUTH,
                        f"roles[{role.name}].inherits_from",
                        f"Role '{role.name}' inherits from non-existent role '{parent}'",
                        auto_fixable=True,
                    )

        # Check RBAC rules reference valid roles
        for rule in auth.rbac:
            if not self._check(rule.role in role_names):
                self._add_error(
                    ValidationLayer.AUTH,
                    f"rbac[{rule.id}].role",
                    f"RBAC rule references non-existent role: {rule.role}",
                    auto_fixable=True,
                )

    # ── Cross-Layer: UI ↔ API ────────────────────────────

    def _validate_ui_api(self, ui: UISchema, api: APISchema) -> None:
        """Validate that UI elements reference existing API endpoints."""
        all_endpoints = api.endpoints + api.auth_endpoints
        api_paths = {ep.path for ep in all_endpoints}

        # Also accept paths with path parameters replaced
        api_path_patterns = set()
        for path in api_paths:
            api_path_patterns.add(path)
            # Add pattern without specific params for matching
            import re
            pattern = re.sub(r'\{[^}]+\}', '{id}', path)
            api_path_patterns.add(pattern)

        # Check form submit endpoints
        for form in ui.forms:
            normalized = form.submit_endpoint.split("?")[0]  # Strip query params
            if not self._check(
                normalized in api_path_patterns
                or any(normalized.rstrip("/") == p.rstrip("/") for p in api_path_patterns)
            ):
                self._add_error(
                    ValidationLayer.CROSS_LAYER,
                    f"ui.forms[{form.id}].submit_endpoint",
                    f"Form submit endpoint '{form.submit_endpoint}' has no matching API endpoint",
                    expected=f"One of: {', '.join(sorted(list(api_paths)[:5]))}...",
                    actual=form.submit_endpoint,
                    fix_suggestion=f"Add API endpoint for {form.submit_endpoint}",
                    auto_fixable=True,
                )

        # Check table data endpoints
        for table in ui.tables:
            normalized = table.data_endpoint.split("?")[0]
            if not self._check(
                normalized in api_path_patterns
                or any(normalized.rstrip("/") == p.rstrip("/") for p in api_path_patterns)
            ):
                self._add_error(
                    ValidationLayer.CROSS_LAYER,
                    f"ui.tables[{table.id}].data_endpoint",
                    f"Table data endpoint '{table.data_endpoint}' has no matching API endpoint",
                    fix_suggestion=f"Add GET API endpoint for {table.data_endpoint}",
                    auto_fixable=True,
                )

    # ── Cross-Layer: API ↔ DB ────────────────────────────

    def _validate_api_db(self, api: APISchema, db: DBSchema) -> None:
        """Validate that API entities have corresponding DB tables."""
        table_entities = set()
        table_names = set()
        for table in db.tables:
            table_entities.add(table.entity.lower())
            table_names.add(table.name.lower())

        for ep in api.endpoints:
            entity_lower = ep.entity.lower()
            # Check entity has a table (by entity name or table name convention)
            entity_match = (
                entity_lower in table_entities
                or f"{entity_lower}s" in table_names
                or entity_lower in table_names
            )
            if not self._check(entity_match):
                self._add_error(
                    ValidationLayer.CROSS_LAYER,
                    f"api.endpoints[{ep.id}].entity",
                    f"API endpoint entity '{ep.entity}' has no corresponding DB table",
                    fix_suggestion=f"Add table for entity '{ep.entity}'",
                    auto_fixable=True,
                )

    # ── Cross-Layer: Auth ↔ All ──────────────────────────

    def _validate_auth_cross(
        self,
        auth: AuthSchema,
        ui: UISchema,
        api: APISchema,
        db: DBSchema,
    ) -> None:
        """Validate auth references across all layers."""
        role_names = {r.name for r in auth.roles}

        # Check UI page roles exist
        for page in ui.pages:
            for role in page.allowed_roles:
                if not self._check(role in role_names):
                    self._add_error(
                        ValidationLayer.CROSS_LAYER,
                        f"ui.pages[{page.id}].allowed_roles",
                        f"Page '{page.id}' references non-existent role: {role}",
                        auto_fixable=True,
                    )

        # Check API endpoint roles exist
        for ep in api.endpoints:
            for role in ep.allowed_roles:
                if not self._check(role in role_names):
                    self._add_error(
                        ValidationLayer.CROSS_LAYER,
                        f"api.endpoints[{ep.id}].allowed_roles",
                        f"Endpoint '{ep.id}' references non-existent role: {role}",
                        auto_fixable=True,
                    )

        # Check auth protected routes match UI pages
        ui_routes = {p.route for p in ui.pages}
        for route in auth.protected_routes:
            if not self._check(route.route in ui_routes):
                self._add_error(
                    ValidationLayer.CROSS_LAYER,
                    f"auth.protected_routes[{route.route}]",
                    f"Protected route '{route.route}' has no corresponding UI page",
                    severity=ValidationSeverity.WARNING,
                    auto_fixable=True,
                )

    # ── Cross-Layer: UI ↔ DB ─────────────────────────────

    def _validate_ui_db(self, ui: UISchema, db: DBSchema) -> None:
        """Validate that UI form fields correspond to DB columns."""
        # Build map of entity → column names
        entity_columns: dict[str, set[str]] = {}
        for table in db.tables:
            entity_columns[table.entity.lower()] = {col.name for col in table.columns}

        for form in ui.forms:
            entity_lower = form.entity.lower()
            if entity_lower in entity_columns:
                db_cols = entity_columns[entity_lower]
                for field in form.fields:
                    # Form fields should correspond to DB columns
                    # (some fields like 'password_confirm' won't match — that's OK)
                    if field.name not in db_cols and not field.name.endswith("_confirm"):
                        self._add_error(
                            ValidationLayer.CROSS_LAYER,
                            f"ui.forms[{form.id}].fields[{field.name}]",
                            f"Form field '{field.name}' has no corresponding DB column in entity '{form.entity}'",
                            severity=ValidationSeverity.WARNING,
                            auto_fixable=True,
                        )
