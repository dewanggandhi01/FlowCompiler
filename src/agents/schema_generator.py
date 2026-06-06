from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, Field

from src.schemas.api_schema import APISchema
from src.schemas.auth_schema import AuthSchema
from src.schemas.db_schema import DBSchema
from src.schemas.system_design_schema import SystemDesign
from src.schemas.ui_schema import UISchema

from .base_agent import AgentResult, BaseAgent, TokenUsage


class GeneratedSchemas(BaseModel):
    ui: UISchema = Field(default_factory=UISchema)
    api: APISchema = Field(default_factory=APISchema)
    db: DBSchema = Field(default_factory=DBSchema)
    auth: AuthSchema = Field(default_factory=AuthSchema)


class _UISchemaAgent(BaseAgent):
    @property
    def system_prompt(self) -> str:
        return """You are a UI schema architect. Generate a complete UISchema from the system design.
Include all pages, forms, tables, and charts. Use IDs: form_{entity}_{action}, table_{entity}_list, page_{name}.
Every form submit_endpoint and table data_endpoint must use /api/v1/ paths from the API design.
Return only the UISchema JSON object with keys: pages, components, forms, tables, charts, theme."""

    def build_user_prompt(self, input_data: Any) -> str:
        return f"Generate UISchema from:\n{self._serialize_input(input_data)}"

    @property
    def output_model(self) -> type[BaseModel]:
        return UISchema


class _APISchemaAgent(BaseAgent):
    @property
    def system_prompt(self) -> str:
        return """You are an API schema architect. Generate a complete APISchema from the system design.
Include CRUD endpoints per entity, auth endpoints (register, login, refresh, logout, me), request/response models.
Use base_path /api/v1 and REST paths like /api/v1/{entities}.
Return only the APISchema JSON object."""

    def build_user_prompt(self, input_data: Any) -> str:
        return f"Generate APISchema from:\n{self._serialize_input(input_data)}"

    @property
    def output_model(self) -> type[BaseModel]:
        return APISchema


class _DBSchemaAgent(BaseAgent):
    @property
    def system_prompt(self) -> str:
        return """You are a database schema architect. Generate a complete DBSchema from the system design.
Include tables with UUID primary keys, foreign keys, indexes, and timestamps.
Return only the DBSchema JSON object with tables, enums, seeds, extensions."""

    def build_user_prompt(self, input_data: Any) -> str:
        return f"Generate DBSchema from:\n{self._serialize_input(input_data)}"

    @property
    def output_model(self) -> type[BaseModel]:
        return DBSchema


class _AuthSchemaAgent(BaseAgent):
    @property
    def system_prompt(self) -> str:
        return """You are an auth schema architect. Generate a complete AuthSchema from the system design.
Include JWT config, roles, permissions, RBAC rules, and protected routes matching UI pages.
Return only the AuthSchema JSON object."""

    def build_user_prompt(self, input_data: Any) -> str:
        return f"Generate AuthSchema from:\n{self._serialize_input(input_data)}"

    @property
    def output_model(self) -> type[BaseModel]:
        return AuthSchema


class SchemaGeneratorAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__()
        self._ui_agent = _UISchemaAgent()
        self._api_agent = _APISchemaAgent()
        self._db_agent = _DBSchemaAgent()
        self._auth_agent = _AuthSchemaAgent()

    @property
    def system_prompt(self) -> str:
        return self._ui_agent.system_prompt

    def build_user_prompt(self, input_data: Any) -> str:
        return self._ui_agent.build_user_prompt(input_data)

    @property
    def output_model(self) -> type[BaseModel]:
        return GeneratedSchemas

    def run(self, input_data: Any) -> AgentResult:
        start = time.time()
        agents = [
            ("ui", self._ui_agent),
            ("api", self._api_agent),
            ("db", self._db_agent),
            ("auth", self._auth_agent),
        ]
        results: dict[str, Any] = {}
        total_usage = TokenUsage()
        total_retries = 0

        for name, agent in agents:
            result = agent.run(input_data)
            results[name] = result.data
            total_usage.prompt_tokens += result.token_usage.prompt_tokens
            total_usage.completion_tokens += result.token_usage.completion_tokens
            total_usage.total_tokens += result.token_usage.total_tokens
            total_retries = max(total_retries, result.retries)

        schemas = GeneratedSchemas(
            ui=results["ui"],
            api=results["api"],
            db=results["db"],
            auth=results["auth"],
        )
        return AgentResult(
            data=schemas,
            token_usage=total_usage,
            duration_ms=(time.time() - start) * 1000,
            retries=total_retries,
            model=self.model,
        )
