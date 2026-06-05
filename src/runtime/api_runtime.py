"""
API Runtime Generator.

Converts API schema into executable FastAPI route configurations
and handler templates.
"""

from __future__ import annotations

from src.schemas.api_schema import APISchema


def generate_api_runtime(api_schema: APISchema) -> dict:
    """
    Convert API schema to executable FastAPI route configurations.

    Generates:
    - Endpoint handler templates
    - Request/response model code
    - Middleware configurations
    - OpenAPI spec metadata
    """
    endpoints = []
    for ep in api_schema.endpoints + api_schema.auth_endpoints:
        handler = _generate_handler_template(ep)
        endpoints.append({
            "id": ep.id,
            "path": ep.path,
            "method": ep.method.value,
            "entity": ep.entity,
            "operation": ep.operation,
            "description": ep.description,
            "requiresAuth": ep.requires_auth,
            "allowedRoles": ep.allowed_roles,
            "requestModelId": ep.request_model_id,
            "responseModelId": ep.response_model_id,
            "successStatus": ep.success_status,
            "rateLimit": ep.rate_limit,
            "handlerTemplate": handler,
        })

    request_models = {}
    for model in api_schema.request_models:
        pydantic_code = _generate_pydantic_model(model, "request")
        request_models[model.id] = {
            "name": model.name,
            "entity": model.entity,
            "fields": [
                {
                    "name": f.name,
                    "fieldType": f.field_type,
                    "required": f.required,
                    "location": f.location.value if hasattr(f.location, "value") else f.location,
                    "validation": f.validation,
                }
                for f in model.fields
            ],
            "pydanticCode": pydantic_code,
        }

    response_models = {}
    for model in api_schema.response_models:
        pydantic_code = _generate_pydantic_model(model, "response")
        response_models[model.id] = {
            "name": model.name,
            "entity": model.entity,
            "responseType": model.response_type.value if hasattr(model.response_type, "value") else model.response_type,
            "fields": [
                {"name": f.name, "fieldType": f.field_type, "nullable": f.nullable}
                for f in model.fields
            ],
            "pydanticCode": pydantic_code,
        }

    middleware = []
    for mw in api_schema.middleware:
        middleware.append({
            "name": mw.name,
            "enabled": mw.enabled,
            "config": mw.config,
        })

    return {
        "basePath": api_schema.base_path,
        "title": api_schema.title,
        "version": api_schema.version,
        "endpoints": endpoints,
        "requestModels": request_models,
        "responseModels": response_models,
        "middleware": middleware,
    }


def _generate_handler_template(ep) -> str:
    """Generate a FastAPI handler code template for an endpoint."""
    method = ep.method.value.lower()
    func_name = ep.id.replace("-", "_").replace(".", "_")
    path = ep.path

    lines = []
    lines.append(f'@router.{method}("{path}")')

    # Build function signature
    params = []
    if ep.path_params:
        for p in ep.path_params:
            params.append(f"{p}: str")
    if ep.request_model_id:
        params.append(f"body: {ep.request_model_id}")
    if ep.requires_auth:
        params.append("current_user: User = Depends(get_current_user)")

    param_str = ", ".join(params)
    lines.append(f"async def {func_name}({param_str}):")
    lines.append(f'    """{ ep.description or ep.summary or ep.operation}"""')

    if ep.operation in ("list", "read"):
        lines.append(f"    # Query {ep.entity} from database")
        lines.append(f"    results = await db.query({ep.entity})")
        lines.append(f"    return results")
    elif ep.operation == "create":
        lines.append(f"    # Create new {ep.entity}")
        lines.append(f"    record = await db.create({ep.entity}, body.dict())")
        lines.append(f"    return record")
    elif ep.operation == "update":
        lines.append(f"    # Update {ep.entity}")
        lines.append(f"    record = await db.update({ep.entity}, id, body.dict())")
        lines.append(f"    return record")
    elif ep.operation == "delete":
        lines.append(f"    # Delete {ep.entity}")
        lines.append(f"    await db.delete({ep.entity}, id)")
        lines.append(f'    return {{"message": "Deleted"}}')
    else:
        lines.append(f"    pass  # Implement {ep.operation}")

    return "\n".join(lines)


def _generate_pydantic_model(model, model_type: str) -> str:
    """Generate Pydantic model code."""
    lines = [f"class {model.name}(BaseModel):"]
    lines.append(f'    """{model.description or model.name}"""')

    fields = model.fields
    for f in fields:
        field_type = _map_field_type(f.field_type)
        if model_type == "response" and hasattr(f, "nullable") and f.nullable:
            field_type = f"Optional[{field_type}]"
        required = getattr(f, "required", True)
        if not required:
            field_type = f"Optional[{field_type}]"
            lines.append(f"    {f.name}: {field_type} = None")
        else:
            lines.append(f"    {f.name}: {field_type}")

    return "\n".join(lines)


def _map_field_type(ft: str) -> str:
    """Map schema field type to Python type."""
    mapping = {
        "string": "str",
        "integer": "int",
        "float": "float",
        "boolean": "bool",
        "date": "date",
        "datetime": "datetime",
        "email": "EmailStr",
        "uuid": "UUID",
        "json": "dict",
        "list": "list",
        "money": "Decimal",
    }
    return mapping.get(ft.lower(), "str")
