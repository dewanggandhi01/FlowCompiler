"""
Shared test fixtures for FlowCompiler tests.

Provides mock data, sample schemas, and test utilities.
All tests use mocked OpenAI responses — never real API calls.
"""

from __future__ import annotations

import pytest

from src.schemas.api_schema import (
    APIEndpoint,
    APISchema,
    HTTPMethod,
    RequestField,
    RequestModel,
    ResponseField,
    ResponseModel,
    ResponseType,
)
from src.schemas.auth_schema import (
    AuthConfig,
    AuthRole,
    AuthSchema,
    Permission,
    PermissionAction,
    ProtectedRoute,
    RBACRule,
)
from src.schemas.db_schema import (
    DBColumn,
    DBIndex,
    DBSchema,
    DBTable,
    ForeignKey,
    IndexType,
    SQLDataType,
)
from src.schemas.intent_schema import (
    Entity,
    EntityField,
    ExtractedIntent,
    Feature,
    FieldType,
    Page,
    PageComponent,
    Role,
)
from src.schemas.ui_schema import (
    FormField,
    InputType,
    TableColumn,
    UIComponent,
    UIForm,
    UIPage,
    UISchema,
    UITable,
    ComponentType,
)


@pytest.fixture
def sample_intent() -> ExtractedIntent:
    """Sample extracted intent for a simple CRM."""
    return ExtractedIntent(
        app_name="TestCRM",
        domain="crm",
        description="A simple CRM application",
        entities=[
            Entity(
                name="User",
                description="Application user",
                fields=[
                    EntityField(name="id", field_type=FieldType.UUID, required=True, unique=True),
                    EntityField(name="email", field_type=FieldType.EMAIL, required=True, unique=True),
                    EntityField(name="password_hash", field_type=FieldType.PASSWORD, required=True),
                    EntityField(name="full_name", field_type=FieldType.STRING, required=True),
                ],
                is_user_entity=True,
            ),
            Entity(
                name="Contact",
                description="A CRM contact",
                fields=[
                    EntityField(name="id", field_type=FieldType.UUID, required=True, unique=True),
                    EntityField(name="first_name", field_type=FieldType.STRING, required=True),
                    EntityField(name="last_name", field_type=FieldType.STRING, required=True),
                    EntityField(name="email", field_type=FieldType.EMAIL, required=False),
                    EntityField(name="phone", field_type=FieldType.PHONE, required=False),
                ],
            ),
        ],
        features=[
            Feature(name="Contact Management", entities_involved=["Contact"]),
            Feature(name="User Authentication", entities_involved=["User"]),
        ],
        roles=[
            Role(name="admin", description="Full access", permissions=["*"]),
            Role(name="user", description="Standard user", is_default=True, permissions=["contacts:read", "contacts:create"]),
        ],
        pages=[
            Page(name="Dashboard", route="/dashboard", requires_auth=True, allowed_roles=["admin", "user"]),
            Page(name="Contacts", route="/contacts", requires_auth=True, allowed_roles=["admin", "user"]),
            Page(name="Login", route="/login", requires_auth=False),
        ],
    )


@pytest.fixture
def sample_ui_schema() -> UISchema:
    """Sample UI schema for testing."""
    return UISchema(
        pages=[
            UIPage(
                id="page_dashboard",
                name="Dashboard",
                route="/dashboard",
                title="Dashboard",
                requires_auth=True,
                allowed_roles=["admin", "user"],
                components=[
                    UIComponent(
                        id="comp_contacts_table",
                        type=ComponentType.TABLE,
                        title="Contacts",
                        entity="Contact",
                        ref_table="table_contacts_list",
                    ),
                ],
            ),
            UIPage(
                id="page_contacts",
                name="Contacts",
                route="/contacts",
                title="Contacts",
                requires_auth=True,
                allowed_roles=["admin", "user"],
                components=[
                    UIComponent(
                        id="comp_contact_form",
                        type=ComponentType.FORM,
                        title="Add Contact",
                        entity="Contact",
                        ref_form="form_contact_create",
                    ),
                ],
            ),
            UIPage(
                id="page_login",
                name="Login",
                route="/login",
                title="Login",
                requires_auth=False,
            ),
        ],
        forms=[
            UIForm(
                id="form_contact_create",
                title="Create Contact",
                entity="Contact",
                submit_endpoint="/api/v1/contacts",
                method="POST",
                fields=[
                    FormField(name="first_name", label="First Name", input_type=InputType.TEXT),
                    FormField(name="last_name", label="Last Name", input_type=InputType.TEXT),
                    FormField(name="email", label="Email", input_type=InputType.EMAIL, required=False),
                ],
            ),
        ],
        tables=[
            UITable(
                id="table_contacts_list",
                title="Contacts",
                entity="Contact",
                data_endpoint="/api/v1/contacts",
                columns=[
                    TableColumn(key="first_name", label="First Name"),
                    TableColumn(key="last_name", label="Last Name"),
                    TableColumn(key="email", label="Email"),
                ],
            ),
        ],
    )


@pytest.fixture
def sample_api_schema() -> APISchema:
    """Sample API schema for testing."""
    return APISchema(
        base_path="/api/v1",
        endpoints=[
            APIEndpoint(
                id="get_contacts_list",
                path="/api/v1/contacts",
                method=HTTPMethod.GET,
                entity="Contact",
                operation="list",
                requires_auth=True,
                allowed_roles=["admin", "user"],
                response_model_id="res_contact_list",
            ),
            APIEndpoint(
                id="post_contacts_create",
                path="/api/v1/contacts",
                method=HTTPMethod.POST,
                entity="Contact",
                operation="create",
                requires_auth=True,
                allowed_roles=["admin", "user"],
                request_model_id="req_contact_create",
                response_model_id="res_contact_single",
                success_status=201,
            ),
        ],
        auth_endpoints=[
            APIEndpoint(
                id="post_auth_login",
                path="/api/v1/auth/login",
                method=HTTPMethod.POST,
                entity="User",
                operation="login",
                requires_auth=False,
            ),
            APIEndpoint(
                id="post_auth_register",
                path="/api/v1/auth/register",
                method=HTTPMethod.POST,
                entity="User",
                operation="register",
                requires_auth=False,
            ),
        ],
        request_models=[
            RequestModel(
                id="req_contact_create",
                name="CreateContactRequest",
                entity="Contact",
                fields=[
                    RequestField(name="first_name", field_type="string"),
                    RequestField(name="last_name", field_type="string"),
                    RequestField(name="email", field_type="email", required=False),
                ],
            ),
        ],
        response_models=[
            ResponseModel(
                id="res_contact_single",
                name="ContactResponse",
                entity="Contact",
                response_type=ResponseType.SINGLE,
                fields=[
                    ResponseField(name="id", field_type="uuid"),
                    ResponseField(name="first_name", field_type="string"),
                    ResponseField(name="last_name", field_type="string"),
                    ResponseField(name="email", field_type="email", nullable=True),
                ],
            ),
            ResponseModel(
                id="res_contact_list",
                name="ContactListResponse",
                entity="Contact",
                response_type=ResponseType.PAGINATED,
                fields=[
                    ResponseField(name="id", field_type="uuid"),
                    ResponseField(name="first_name", field_type="string"),
                    ResponseField(name="last_name", field_type="string"),
                ],
            ),
        ],
    )


@pytest.fixture
def sample_db_schema() -> DBSchema:
    """Sample DB schema for testing."""
    return DBSchema(
        tables=[
            DBTable(
                name="users",
                entity="User",
                columns=[
                    DBColumn(name="id", data_type=SQLDataType.UUID, primary_key=True, default="uuid_generate_v4()"),
                    DBColumn(name="email", data_type=SQLDataType.VARCHAR, length=255, unique=True),
                    DBColumn(name="password_hash", data_type=SQLDataType.VARCHAR, length=255),
                    DBColumn(name="full_name", data_type=SQLDataType.VARCHAR, length=255),
                ],
                indexes=[
                    DBIndex(name="idx_users_email", columns=["email"], unique=True),
                ],
            ),
            DBTable(
                name="contacts",
                entity="Contact",
                columns=[
                    DBColumn(name="id", data_type=SQLDataType.UUID, primary_key=True, default="uuid_generate_v4()"),
                    DBColumn(name="first_name", data_type=SQLDataType.VARCHAR, length=100),
                    DBColumn(name="last_name", data_type=SQLDataType.VARCHAR, length=100),
                    DBColumn(name="email", data_type=SQLDataType.VARCHAR, length=255, nullable=True),
                    DBColumn(name="phone", data_type=SQLDataType.VARCHAR, length=50, nullable=True),
                    DBColumn(name="user_id", data_type=SQLDataType.UUID),
                ],
                foreign_keys=[
                    ForeignKey(column="user_id", references_table="users", references_column="id"),
                ],
            ),
        ],
    )


@pytest.fixture
def sample_auth_schema() -> AuthSchema:
    """Sample auth schema for testing."""
    return AuthSchema(
        roles=[
            AuthRole(
                name="admin",
                description="Full access",
                is_admin=True,
                permissions=["contacts:create", "contacts:read", "contacts:update", "contacts:delete"],
            ),
            AuthRole(
                name="user",
                description="Standard user",
                is_default=True,
                permissions=["contacts:read", "contacts:create"],
            ),
        ],
        permissions=[
            Permission(id="contacts:create", entity="Contact", action=PermissionAction.CREATE),
            Permission(id="contacts:read", entity="Contact", action=PermissionAction.READ),
            Permission(id="contacts:update", entity="Contact", action=PermissionAction.UPDATE),
            Permission(id="contacts:delete", entity="Contact", action=PermissionAction.DELETE),
        ],
        rbac=[
            RBACRule(id="rbac_admin_contacts_all", role="admin", entity="Contact", action=PermissionAction.ALL),
            RBACRule(id="rbac_user_contacts_read", role="user", entity="Contact", action=PermissionAction.READ),
        ],
        protected_routes=[
            ProtectedRoute(route="/dashboard", allowed_roles=["admin", "user"]),
            ProtectedRoute(route="/contacts", allowed_roles=["admin", "user"]),
        ],
    )
