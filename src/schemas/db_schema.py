"""
Database Schema — Stage 3C output.

Defines the structured output for the DB portion of the Schema Generation Agent.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────


class SQLDataType(str, Enum):
    UUID = "UUID"
    SERIAL = "SERIAL"
    BIGSERIAL = "BIGSERIAL"
    VARCHAR = "VARCHAR"
    TEXT = "TEXT"
    INTEGER = "INTEGER"
    BIGINT = "BIGINT"
    FLOAT = "FLOAT"
    DECIMAL = "DECIMAL"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    TIMESTAMP = "TIMESTAMP"
    TIMESTAMPTZ = "TIMESTAMPTZ"
    JSON = "JSON"
    JSONB = "JSONB"
    BYTEA = "BYTEA"
    ENUM = "ENUM"


class ConstraintType(str, Enum):
    PRIMARY_KEY = "PRIMARY KEY"
    FOREIGN_KEY = "FOREIGN KEY"
    UNIQUE = "UNIQUE"
    CHECK = "CHECK"
    NOT_NULL = "NOT NULL"
    DEFAULT = "DEFAULT"


class IndexType(str, Enum):
    BTREE = "btree"
    HASH = "hash"
    GIN = "gin"
    GIST = "gist"
    BRIN = "brin"


class OnDeleteAction(str, Enum):
    CASCADE = "CASCADE"
    SET_NULL = "SET NULL"
    SET_DEFAULT = "SET DEFAULT"
    RESTRICT = "RESTRICT"
    NO_ACTION = "NO ACTION"


# ── Sub-models ───────────────────────────────────────────


class DBColumn(BaseModel):
    """A single column in a database table."""
    name: str = Field(..., description="Column name in snake_case")
    data_type: SQLDataType
    length: Optional[int] = Field(default=None, description="Length for VARCHAR")
    precision: Optional[int] = Field(default=None, description="Precision for DECIMAL")
    scale: Optional[int] = Field(default=None, description="Scale for DECIMAL")
    nullable: bool = Field(default=False)
    primary_key: bool = Field(default=False)
    unique: bool = Field(default=False)
    default: Optional[str] = Field(default=None, description="Default value as SQL expression")
    enum_values: list[str] = Field(default_factory=list, description="Values if type is ENUM")
    description: str = Field(default="")


class ForeignKey(BaseModel):
    """A foreign key constraint."""
    column: str = Field(..., description="Column in this table")
    references_table: str = Field(..., description="Referenced table name")
    references_column: str = Field(default="id", description="Referenced column name")
    on_delete: OnDeleteAction = Field(default=OnDeleteAction.CASCADE)
    on_update: OnDeleteAction = Field(default=OnDeleteAction.CASCADE)


class DBConstraint(BaseModel):
    """A database constraint."""
    name: str = Field(..., description="Constraint name")
    type: ConstraintType
    columns: list[str] = Field(default_factory=list)
    expression: Optional[str] = Field(default=None, description="CHECK constraint expression")
    foreign_key: Optional[ForeignKey] = None


class DBIndex(BaseModel):
    """A database index."""
    name: str = Field(..., description="Index name")
    columns: list[str] = Field(default_factory=list)
    index_type: IndexType = Field(default=IndexType.BTREE)
    unique: bool = Field(default=False)
    condition: Optional[str] = Field(default=None, description="Partial index WHERE condition")


class DBTable(BaseModel):
    """A database table definition."""
    name: str = Field(..., description="Table name in snake_case")
    entity: str = Field(..., description="Entity this table represents (PascalCase)")
    description: str = Field(default="")
    columns: list[DBColumn] = Field(default_factory=list)
    foreign_keys: list[ForeignKey] = Field(default_factory=list)
    constraints: list[DBConstraint] = Field(default_factory=list)
    indexes: list[DBIndex] = Field(default_factory=list)
    timestamps: bool = Field(
        default=True,
        description="Auto-add created_at and updated_at columns",
    )


class DBEnum(BaseModel):
    """A PostgreSQL ENUM type definition."""
    name: str = Field(..., description="Enum type name")
    values: list[str] = Field(default_factory=list)


class SeedRecord(BaseModel):
    data: str = Field(default="{}", description="JSON object string for one seed record")


class Seed(BaseModel):
    """Seed data for a table."""
    table: str
    records: list[SeedRecord] = Field(default_factory=list)


# ── Main Output ──────────────────────────────────────────


class DBSchema(BaseModel):
    """
    Stage 3C Output: Complete database schema.

    Defines all tables, columns, constraints, indexes, and enums
    for the PostgreSQL database.
    """
    tables: list[DBTable] = Field(default_factory=list)
    enums: list[DBEnum] = Field(default_factory=list)
    seeds: list[Seed] = Field(
        default_factory=list,
        description="Initial seed data (e.g., default roles)",
    )
    extensions: list[str] = Field(
        default_factory=lambda: ["uuid-ossp"],
        description="PostgreSQL extensions to enable",
    )
