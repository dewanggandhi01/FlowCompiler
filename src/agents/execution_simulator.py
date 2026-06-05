"""
Execution Simulator — Stage 6.

Simulates runtime execution to verify the generated configuration
would actually work when deployed.

Checks:
- Form submission paths
- Endpoint existence and reachability
- DB table integrity
- Permission resolution
- Route reachability
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from src.schemas.api_schema import APISchema
from src.schemas.auth_schema import AuthSchema
from src.schemas.db_schema import DBSchema
from src.schemas.runtime_schema import RuntimeIssue, RuntimeSimulationResult, RuntimeStatus
from src.schemas.ui_schema import UISchema

logger = logging.getLogger(__name__)


class ExecutionSimulator:
    """
    Stage 6: Execution Simulator.

    Simulates runtime execution without actually running the application.
    Checks that all pieces connect properly and would work at runtime.
    """

    def __init__(self) -> None:
        self.issues: list[RuntimeIssue] = []
        self.total_checks = 0
        self.passed_checks = 0

    def simulate(
        self,
        ui: UISchema,
        api: APISchema,
        db: DBSchema,
        auth: AuthSchema,
    ) -> RuntimeSimulationResult:
        """
        Run full runtime simulation.

        Returns RuntimeSimulationResult with pass/fail status and issues.
        """
        self.issues = []
        self.total_checks = 0
        self.passed_checks = 0

        self._simulate_form_submissions(ui, api)
        self._simulate_endpoint_resolution(api, db)
        self._simulate_db_integrity(db)
        self._simulate_permission_resolution(auth, api, ui)
        self._simulate_route_reachability(ui, auth)
        self._simulate_data_flow(ui, api, db)

        failed = len([i for i in self.issues if i.severity == "error"])
        if failed == 0:
            status = RuntimeStatus.PASS
        elif failed < self.total_checks // 2:
            status = RuntimeStatus.PARTIAL
        else:
            status = RuntimeStatus.FAIL

        result = RuntimeSimulationResult(
            runtime_status=status,
            issues=self.issues,
            simulated_checks=self.total_checks,
            passed_checks=self.passed_checks,
            failed_checks=failed,
            simulation_details={
                "form_submissions": self._count_by_category("form_submission"),
                "endpoint_resolution": self._count_by_category("endpoint_resolution"),
                "db_integrity": self._count_by_category("db_integrity"),
                "permission_resolution": self._count_by_category("permission_resolution"),
                "route_reachability": self._count_by_category("route_reachability"),
                "data_flow": self._count_by_category("data_flow"),
            },
        )

        logger.info(
            f"Simulation {status.value}: {self.passed_checks}/{self.total_checks} "
            f"checks passed, {failed} issues"
        )

        return result

    # ── Helpers ───────────────────────────────────────────

    def _add_issue(
        self,
        category: str,
        description: str,
        component: str = "",
        severity: str = "error",
        suggestion: str = "",
    ) -> None:
        self.issues.append(
            RuntimeIssue(
                id=f"sim_{uuid.uuid4().hex[:8]}",
                category=category,
                severity=severity,
                description=description,
                component=component,
                suggestion=suggestion,
            )
        )

    def _check(self, passed: bool) -> bool:
        self.total_checks += 1
        if passed:
            self.passed_checks += 1
        return passed

    def _count_by_category(self, category: str) -> dict[str, int]:
        cat_issues = [i for i in self.issues if i.category == category]
        return {
            "errors": len([i for i in cat_issues if i.severity == "error"]),
            "warnings": len([i for i in cat_issues if i.severity == "warning"]),
        }

    # ── Simulation Checks ────────────────────────────────

    def _simulate_form_submissions(self, ui: UISchema, api: APISchema) -> None:
        """Can all forms submit successfully?"""
        all_endpoints = api.endpoints + api.auth_endpoints
        api_endpoints = {}
        for ep in all_endpoints:
            key = (ep.path.rstrip("/"), ep.method.value)
            api_endpoints[key] = ep

        for form in ui.forms:
            path = form.submit_endpoint.rstrip("/")
            method = form.method.upper()

            # Check endpoint exists
            matching_ep = api_endpoints.get((path, method))
            if not matching_ep:
                # Try without exact match
                matching_ep = next(
                    (ep for ep in all_endpoints if ep.path.rstrip("/") == path),
                    None,
                )

            if not self._check(matching_ep is not None):
                self._add_issue(
                    "form_submission",
                    f"Form '{form.id}' submits to {method} {path} but no matching endpoint exists",
                    component=f"form:{form.id}",
                    suggestion=f"Create {method} {path} endpoint",
                )
                continue

            # Check form fields match request model
            if matching_ep and matching_ep.request_model_id:
                req_model = next(
                    (m for m in api.request_models if m.id == matching_ep.request_model_id),
                    None,
                )
                if req_model:
                    req_fields = {f.name for f in req_model.fields}
                    form_fields = {f.name for f in form.fields}
                    missing = req_fields - form_fields - {"id", "created_at", "updated_at"}
                    if missing:
                        if not self._check(False):
                            self._add_issue(
                                "form_submission",
                                f"Form '{form.id}' is missing required fields: {missing}",
                                component=f"form:{form.id}",
                                severity="warning",
                                suggestion=f"Add fields {missing} to form",
                            )
                    else:
                        self._check(True)

    def _simulate_endpoint_resolution(self, api: APISchema, db: DBSchema) -> None:
        """Do all endpoints resolve to valid DB operations?"""
        table_names = {t.name.lower() for t in db.tables}
        table_entities = {t.entity.lower() for t in db.tables}

        for ep in api.endpoints:
            entity_lower = ep.entity.lower()
            has_table = (
                entity_lower in table_entities
                or f"{entity_lower}s" in table_names
                or entity_lower in table_names
            )

            if not self._check(has_table):
                self._add_issue(
                    "endpoint_resolution",
                    f"Endpoint '{ep.id}' ({ep.method.value} {ep.path}) targets entity "
                    f"'{ep.entity}' with no DB table",
                    component=f"endpoint:{ep.id}",
                    suggestion=f"Create table for entity '{ep.entity}'",
                )

    def _simulate_db_integrity(self, db: DBSchema) -> None:
        """Are all DB tables valid and internally consistent?"""
        table_names = {t.name for t in db.tables}

        for table in db.tables:
            # Check has PK
            has_pk = any(c.primary_key for c in table.columns)
            if not self._check(has_pk):
                self._add_issue(
                    "db_integrity",
                    f"Table '{table.name}' has no primary key",
                    component=f"table:{table.name}",
                    suggestion="Add 'id' column as primary key",
                )

            # Check FKs resolve
            for fk in table.foreign_keys:
                if not self._check(fk.references_table in table_names):
                    self._add_issue(
                        "db_integrity",
                        f"Table '{table.name}' has FK to non-existent table '{fk.references_table}'",
                        component=f"table:{table.name}",
                        suggestion=f"Create table '{fk.references_table}' or fix FK reference",
                    )

                # Check FK column exists in table
                col_names = {c.name for c in table.columns}
                if not self._check(fk.column in col_names):
                    self._add_issue(
                        "db_integrity",
                        f"Table '{table.name}' FK column '{fk.column}' does not exist",
                        component=f"table:{table.name}",
                        suggestion=f"Add column '{fk.column}' to table '{table.name}'",
                    )

    def _simulate_permission_resolution(
        self, auth: AuthSchema, api: APISchema, ui: UISchema
    ) -> None:
        """Can all permissions be resolved at runtime?"""
        role_names = {r.name for r in auth.roles}
        permission_ids = {p.id for p in auth.permissions}

        # Check each protected endpoint has valid roles
        for ep in api.endpoints:
            if ep.requires_auth and ep.allowed_roles:
                for role in ep.allowed_roles:
                    if not self._check(role in role_names):
                        self._add_issue(
                            "permission_resolution",
                            f"Endpoint '{ep.id}' allows role '{role}' which doesn't exist",
                            component=f"endpoint:{ep.id}",
                            suggestion=f"Add role '{role}' to auth schema",
                        )

        # Check RBAC rules can resolve
        for rule in auth.rbac:
            if not self._check(rule.role in role_names):
                self._add_issue(
                    "permission_resolution",
                    f"RBAC rule '{rule.id}' references non-existent role '{rule.role}'",
                    component=f"rbac:{rule.id}",
                )

    def _simulate_route_reachability(self, ui: UISchema, auth: AuthSchema) -> None:
        """Are all routes reachable by at least one role?"""
        role_names = {r.name for r in auth.roles}

        for page in ui.pages:
            if page.requires_auth:
                if page.allowed_roles:
                    # Check at least one role exists
                    valid_roles = [r for r in page.allowed_roles if r in role_names]
                    if not self._check(len(valid_roles) > 0):
                        self._add_issue(
                            "route_reachability",
                            f"Page '{page.id}' ({page.route}) is unreachable — "
                            f"none of its allowed roles {page.allowed_roles} exist",
                            component=f"page:{page.id}",
                            suggestion="Add valid roles or make the page public",
                        )
                    else:
                        self._check(True)
                else:
                    # Auth required but no roles specified — accessible to all authenticated
                    self._check(True)
            else:
                # Public page
                self._check(True)

    def _simulate_data_flow(self, ui: UISchema, api: APISchema, db: DBSchema) -> None:
        """Simulate end-to-end data flow: UI → API → DB."""
        all_endpoints = api.endpoints + api.auth_endpoints

        for table in ui.tables:
            # Table → API endpoint
            matching_ep = next(
                (ep for ep in all_endpoints if ep.path.rstrip("/") == table.data_endpoint.rstrip("/")),
                None,
            )

            if matching_ep:
                # API endpoint → DB table
                entity = matching_ep.entity.lower()
                has_table = any(
                    t.entity.lower() == entity or t.name.lower() == entity or t.name.lower() == f"{entity}s"
                    for t in db.tables
                )
                if self._check(has_table):
                    # Check table columns match UI table columns
                    db_table = next(
                        (t for t in db.tables if t.entity.lower() == entity or t.name.lower() == f"{entity}s"),
                        None,
                    )
                    if db_table:
                        db_col_names = {c.name for c in db_table.columns}
                        for col in table.columns:
                            if col.key not in db_col_names and col.key not in ("actions",):
                                self._add_issue(
                                    "data_flow",
                                    f"Table '{table.id}' column '{col.key}' not found in DB table",
                                    component=f"table:{table.id}",
                                    severity="warning",
                                )
                else:
                    self._add_issue(
                        "data_flow",
                        f"Table '{table.id}' → endpoint '{matching_ep.id}' → "
                        f"no DB table for entity '{matching_ep.entity}'",
                        component=f"table:{table.id}",
                    )
            else:
                if not self._check(False):
                    self._add_issue(
                        "data_flow",
                        f"Table '{table.id}' data_endpoint '{table.data_endpoint}' has no matching API endpoint",
                        component=f"table:{table.id}",
                        severity="warning",
                    )
