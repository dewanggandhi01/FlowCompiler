"""Tests for the Execution Simulator."""

import pytest

from src.agents.execution_simulator import ExecutionSimulator
from src.schemas.api_schema import APIEndpoint, APISchema, HTTPMethod
from src.schemas.auth_schema import AuthRole, AuthSchema
from src.schemas.db_schema import DBColumn, DBSchema, DBTable, ForeignKey, SQLDataType
from src.schemas.runtime_schema import RuntimeStatus
from src.schemas.ui_schema import (
    FormField, InputType, UIForm, UIPage, UISchema, UITable, TableColumn,
)


class TestSimulationPass:
    """Test cases where simulation should pass."""

    def test_valid_schemas_simulate(self, sample_ui_schema, sample_api_schema, sample_db_schema, sample_auth_schema):
        sim = ExecutionSimulator()
        result = sim.simulate(sample_ui_schema, sample_api_schema, sample_db_schema, sample_auth_schema)
        assert result.simulated_checks > 0
        assert result.passed_checks > 0


class TestFormSubmissionSimulation:
    """Test form submission simulation."""

    def test_missing_endpoint(self, sample_api_schema, sample_db_schema, sample_auth_schema):
        ui = UISchema(
            forms=[
                UIForm(
                    id="form_broken", title="Broken", entity="X",
                    submit_endpoint="/api/v1/nonexistent", method="POST",
                    fields=[FormField(name="x", label="X", input_type=InputType.TEXT)],
                ),
            ],
        )
        sim = ExecutionSimulator()
        result = sim.simulate(ui, sample_api_schema, sample_db_schema, sample_auth_schema)
        form_issues = [i for i in result.issues if i.category == "form_submission"]
        assert len(form_issues) > 0


class TestDBIntegritySimulation:
    """Test DB integrity simulation."""

    def test_missing_pk_detected(self, sample_ui_schema, sample_api_schema, sample_auth_schema):
        db = DBSchema(
            tables=[
                DBTable(
                    name="broken", entity="Broken",
                    columns=[DBColumn(name="x", data_type=SQLDataType.VARCHAR, length=100)],
                ),
            ],
        )
        sim = ExecutionSimulator()
        result = sim.simulate(sample_ui_schema, sample_api_schema, db, sample_auth_schema)
        db_issues = [i for i in result.issues if i.category == "db_integrity"]
        assert len(db_issues) > 0

    def test_broken_fk(self, sample_ui_schema, sample_api_schema, sample_auth_schema):
        db = DBSchema(
            tables=[
                DBTable(
                    name="items", entity="Item",
                    columns=[
                        DBColumn(name="id", data_type=SQLDataType.UUID, primary_key=True),
                        DBColumn(name="ghost_id", data_type=SQLDataType.UUID),
                    ],
                    foreign_keys=[ForeignKey(column="ghost_id", references_table="ghost")],
                ),
            ],
        )
        sim = ExecutionSimulator()
        result = sim.simulate(sample_ui_schema, sample_api_schema, db, sample_auth_schema)
        fk_issues = [i for i in result.issues if "non-existent table" in i.description]
        assert len(fk_issues) > 0


class TestRouteReachabilitySimulation:
    """Test route reachability simulation."""

    def test_unreachable_page(self, sample_api_schema, sample_db_schema):
        ui = UISchema(
            pages=[
                UIPage(
                    id="page_locked", name="Locked", route="/locked", title="Locked",
                    requires_auth=True, allowed_roles=["ghost_role"],
                ),
            ],
        )
        auth = AuthSchema(
            roles=[AuthRole(name="user", is_default=True)],
        )
        sim = ExecutionSimulator()
        result = sim.simulate(ui, sample_api_schema, sample_db_schema, auth)
        route_issues = [i for i in result.issues if i.category == "route_reachability"]
        assert len(route_issues) > 0


class TestAPITests:
    """Tests for FastAPI endpoints."""

    def test_health_check(self):
        from fastapi.testclient import TestClient
        from src.app import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_generate_missing_prompt(self):
        from fastapi.testclient import TestClient
        from src.app import app
        client = TestClient(app)
        response = client.post("/generate", json={})
        assert response.status_code == 422  # Validation error

    def test_validate_empty(self):
        from fastapi.testclient import TestClient
        from src.app import app
        client = TestClient(app)
        response = client.post("/validate", json={"ui": {}, "api": {}, "db": {}, "auth": {}})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("PASS", "FAIL")
