"""Tests for Pydantic schema models."""

import pytest
from pydantic import ValidationError

from src.schemas.intent_schema import (
    Entity, EntityField, ExtractedIntent, FieldType, DomainType, Feature, Role, Page,
)
from src.schemas.ui_schema import UISchema, UIPage, UIForm, FormField, InputType
from src.schemas.api_schema import APISchema, APIEndpoint, HTTPMethod
from src.schemas.db_schema import DBSchema, DBTable, DBColumn, SQLDataType
from src.schemas.auth_schema import AuthSchema, AuthRole, Permission, PermissionAction
from src.schemas.validation_schema import ValidationResult, ValidationErrorDetail, ValidationLayer
from src.schemas.runtime_schema import CompilerOutput, RuntimeConfig


class TestIntentSchema:
    """Tests for ExtractedIntent model."""

    def test_valid_intent(self, sample_intent):
        assert sample_intent.app_name == "TestCRM"
        assert sample_intent.domain == DomainType.CRM
        assert len(sample_intent.entities) == 2
        assert len(sample_intent.roles) == 2

    def test_intent_serialization(self, sample_intent):
        data = sample_intent.model_dump()
        restored = ExtractedIntent.model_validate(data)
        assert restored.app_name == sample_intent.app_name
        assert len(restored.entities) == len(sample_intent.entities)

    def test_intent_json_round_trip(self, sample_intent):
        json_str = sample_intent.model_dump_json()
        restored = ExtractedIntent.model_validate_json(json_str)
        assert restored == sample_intent

    def test_entity_field_types(self):
        field = EntityField(name="email", field_type=FieldType.EMAIL)
        assert field.field_type == FieldType.EMAIL
        assert field.required is True
        assert field.unique is False

    def test_entity_with_all_fields(self):
        entity = Entity(
            name="Product",
            description="A product entity",
            fields=[
                EntityField(name="id", field_type=FieldType.UUID, unique=True),
                EntityField(name="name", field_type=FieldType.STRING),
                EntityField(name="price", field_type=FieldType.MONEY),
                EntityField(name="active", field_type=FieldType.BOOLEAN),
            ],
        )
        assert len(entity.fields) == 4
        assert entity.fields[2].field_type == FieldType.MONEY

    def test_minimal_intent(self):
        intent = ExtractedIntent(app_name="Test", domain=DomainType.CUSTOM)
        assert intent.app_name == "Test"
        assert len(intent.entities) == 0
        assert len(intent.assumptions) == 0


class TestUISchema:
    """Tests for UISchema model."""

    def test_valid_ui(self, sample_ui_schema):
        assert len(sample_ui_schema.pages) == 3
        assert len(sample_ui_schema.forms) == 1
        assert len(sample_ui_schema.tables) == 1

    def test_page_routes(self, sample_ui_schema):
        routes = [p.route for p in sample_ui_schema.pages]
        assert "/dashboard" in routes
        assert "/contacts" in routes
        assert "/login" in routes

    def test_form_fields(self, sample_ui_schema):
        form = sample_ui_schema.forms[0]
        assert form.entity == "Contact"
        assert len(form.fields) == 3

    def test_empty_ui(self):
        ui = UISchema()
        assert len(ui.pages) == 0
        assert ui.theme.mode == "dark"


class TestAPISchema:
    """Tests for APISchema model."""

    def test_valid_api(self, sample_api_schema):
        assert len(sample_api_schema.endpoints) == 2
        assert len(sample_api_schema.auth_endpoints) == 2

    def test_endpoint_methods(self, sample_api_schema):
        get_ep = sample_api_schema.endpoints[0]
        assert get_ep.method == HTTPMethod.GET
        assert get_ep.operation == "list"


class TestDBSchema:
    """Tests for DBSchema model."""

    def test_valid_db(self, sample_db_schema):
        assert len(sample_db_schema.tables) == 2
        table_names = [t.name for t in sample_db_schema.tables]
        assert "users" in table_names
        assert "contacts" in table_names

    def test_primary_keys(self, sample_db_schema):
        for table in sample_db_schema.tables:
            pks = [c for c in table.columns if c.primary_key]
            assert len(pks) >= 1, f"Table {table.name} has no primary key"

    def test_foreign_keys(self, sample_db_schema):
        contacts = next(t for t in sample_db_schema.tables if t.name == "contacts")
        assert len(contacts.foreign_keys) == 1
        assert contacts.foreign_keys[0].references_table == "users"


class TestAuthSchema:
    """Tests for AuthSchema model."""

    def test_valid_auth(self, sample_auth_schema):
        assert len(sample_auth_schema.roles) == 2
        assert len(sample_auth_schema.permissions) == 4

    def test_default_role(self, sample_auth_schema):
        defaults = [r for r in sample_auth_schema.roles if r.is_default]
        assert len(defaults) == 1
        assert defaults[0].name == "user"

    def test_admin_role(self, sample_auth_schema):
        admin = next(r for r in sample_auth_schema.roles if r.name == "admin")
        assert admin.is_admin is True


class TestValidationResult:
    """Tests for ValidationResult model."""

    def test_pass_result(self):
        result = ValidationResult(status="PASS", total_checks=10, passed_checks=10, failed_checks=0)
        assert result.error_count == 0
        assert result.status == "PASS"

    def test_fail_result(self):
        error = ValidationErrorDetail(
            id="err_001", layer=ValidationLayer.DB, message="Missing PK"
        )
        result = ValidationResult(
            status="FAIL", errors=[error], total_checks=10, passed_checks=9, failed_checks=1
        )
        assert result.error_count == 1
        assert result.has_errors_in_layer(ValidationLayer.DB)
        assert not result.has_errors_in_layer(ValidationLayer.UI)

    def test_status_pattern(self):
        with pytest.raises(ValidationError):
            ValidationResult(status="INVALID", total_checks=0, passed_checks=0, failed_checks=0)


class TestCompilerOutput:
    """Tests for CompilerOutput model."""

    def test_minimal_output(self):
        output = CompilerOutput(
            compile_id="test_001",
            original_prompt="Build a CRM",
        )
        assert output.status == "completed"
        assert output.total_tokens == 0

    def test_runtime_config(self, sample_ui_schema, sample_api_schema, sample_db_schema, sample_auth_schema):
        config = RuntimeConfig(
            ui=sample_ui_schema,
            api=sample_api_schema,
            db=sample_db_schema,
            auth=sample_auth_schema,
        )
        assert len(config.ui.pages) == 3
        assert len(config.api.endpoints) == 2
