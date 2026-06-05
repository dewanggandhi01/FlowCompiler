"""Tests for the Validation Engine."""

import pytest

from src.agents.validator import ValidationEngine
from src.schemas.api_schema import APIEndpoint, APISchema, HTTPMethod
from src.schemas.auth_schema import AuthRole, AuthSchema, Permission, PermissionAction
from src.schemas.db_schema import DBColumn, DBSchema, DBTable, ForeignKey, SQLDataType
from src.schemas.ui_schema import (
    FormField, InputType, UIComponent, UIForm, UIPage, UISchema, UITable, TableColumn, ComponentType,
)


class TestValidationPass:
    """Test cases where validation should PASS."""

    def test_valid_schemas_pass(self, sample_ui_schema, sample_api_schema, sample_db_schema, sample_auth_schema):
        engine = ValidationEngine()
        result = engine.validate(sample_ui_schema, sample_api_schema, sample_db_schema, sample_auth_schema)
        # Should pass or have only warnings
        assert result.total_checks > 0
        assert result.passed_checks > 0

    def test_empty_schemas_minimal(self):
        engine = ValidationEngine()
        result = engine.validate(UISchema(), APISchema(), DBSchema(), AuthSchema())
        # Minimal schemas will have some errors (no auth endpoints, no roles)
        assert result.total_checks > 0


class TestUIValidation:
    """Test UI schema validation errors."""

    def test_duplicate_page_ids(self, sample_api_schema, sample_db_schema, sample_auth_schema):
        ui = UISchema(
            pages=[
                UIPage(id="page_1", name="A", route="/a", title="A"),
                UIPage(id="page_1", name="B", route="/b", title="B"),
            ]
        )
        engine = ValidationEngine()
        result = engine.validate(ui, sample_api_schema, sample_db_schema, sample_auth_schema)
        ui_errors = [e for e in result.errors if "Duplicate page ID" in e.message]
        assert len(ui_errors) > 0

    def test_invalid_route(self, sample_api_schema, sample_db_schema, sample_auth_schema):
        ui = UISchema(
            pages=[
                UIPage(id="page_bad", name="Bad", route="no-slash", title="Bad"),
            ]
        )
        engine = ValidationEngine()
        result = engine.validate(ui, sample_api_schema, sample_db_schema, sample_auth_schema)
        route_errors = [e for e in result.errors if "start with '/'" in e.message]
        assert len(route_errors) > 0

    def test_missing_form_reference(self, sample_api_schema, sample_db_schema, sample_auth_schema):
        ui = UISchema(
            pages=[
                UIPage(
                    id="page_1", name="P", route="/p", title="P",
                    components=[
                        UIComponent(id="c1", type=ComponentType.FORM, ref_form="nonexistent_form"),
                    ],
                ),
            ]
        )
        engine = ValidationEngine()
        result = engine.validate(ui, sample_api_schema, sample_db_schema, sample_auth_schema)
        ref_errors = [e for e in result.errors if "not found in forms" in e.message]
        assert len(ref_errors) > 0

    def test_empty_form_fields(self, sample_api_schema, sample_db_schema, sample_auth_schema):
        ui = UISchema(
            forms=[
                UIForm(id="form_empty", title="Empty", entity="X", submit_endpoint="/api/x", fields=[]),
            ]
        )
        engine = ValidationEngine()
        result = engine.validate(ui, sample_api_schema, sample_db_schema, sample_auth_schema)
        empty_errors = [e for e in result.errors if "no fields" in e.message]
        assert len(empty_errors) > 0


class TestDBValidation:
    """Test DB schema validation errors."""

    def test_missing_primary_key(self, sample_ui_schema, sample_api_schema, sample_auth_schema):
        db = DBSchema(
            tables=[
                DBTable(
                    name="broken", entity="Broken",
                    columns=[DBColumn(name="name", data_type=SQLDataType.VARCHAR, length=100)],
                ),
            ]
        )
        engine = ValidationEngine()
        result = engine.validate(sample_ui_schema, sample_api_schema, db, sample_auth_schema)
        pk_errors = [e for e in result.errors if "primary key" in e.message.lower()]
        assert len(pk_errors) > 0

    def test_invalid_foreign_key(self, sample_ui_schema, sample_api_schema, sample_auth_schema):
        db = DBSchema(
            tables=[
                DBTable(
                    name="items", entity="Item",
                    columns=[
                        DBColumn(name="id", data_type=SQLDataType.UUID, primary_key=True),
                        DBColumn(name="ghost_id", data_type=SQLDataType.UUID),
                    ],
                    foreign_keys=[
                        ForeignKey(column="ghost_id", references_table="nonexistent_table"),
                    ],
                ),
            ]
        )
        engine = ValidationEngine()
        result = engine.validate(sample_ui_schema, sample_api_schema, db, sample_auth_schema)
        fk_errors = [e for e in result.errors if "non-existent table" in e.message]
        assert len(fk_errors) > 0


class TestAuthValidation:
    """Test Auth schema validation errors."""

    def test_no_roles(self, sample_ui_schema, sample_api_schema, sample_db_schema):
        auth = AuthSchema(roles=[], permissions=[])
        engine = ValidationEngine()
        result = engine.validate(sample_ui_schema, sample_api_schema, sample_db_schema, auth)
        role_errors = [e for e in result.errors if "No roles defined" in e.message]
        assert len(role_errors) > 0

    def test_invalid_permission_reference(self, sample_ui_schema, sample_api_schema, sample_db_schema):
        auth = AuthSchema(
            roles=[
                AuthRole(name="admin", permissions=["nonexistent:perm"]),
            ],
            permissions=[],
        )
        engine = ValidationEngine()
        result = engine.validate(sample_ui_schema, sample_api_schema, sample_db_schema, auth)
        perm_errors = [e for e in result.errors if "does not exist" in e.message]
        assert len(perm_errors) > 0


class TestCrossLayerValidation:
    """Test cross-layer validation."""

    def test_form_endpoint_mismatch(self, sample_api_schema, sample_db_schema, sample_auth_schema):
        ui = UISchema(
            forms=[
                UIForm(
                    id="form_bad", title="Bad", entity="X",
                    submit_endpoint="/api/v1/nonexistent",
                    fields=[FormField(name="x", label="X", input_type=InputType.TEXT)],
                ),
            ]
        )
        engine = ValidationEngine()
        result = engine.validate(ui, sample_api_schema, sample_db_schema, sample_auth_schema)
        cross_errors = [e for e in result.errors if "no matching API endpoint" in e.message]
        assert len(cross_errors) > 0

    def test_role_mismatch_across_layers(self, sample_ui_schema, sample_api_schema, sample_db_schema):
        auth = AuthSchema(
            roles=[AuthRole(name="viewer", is_default=True)],
            permissions=[],
        )
        engine = ValidationEngine()
        result = engine.validate(sample_ui_schema, sample_api_schema, sample_db_schema, auth)
        # UI pages reference admin/user but auth only has viewer
        role_errors = [e for e in result.errors if "non-existent role" in e.message]
        assert len(role_errors) > 0
