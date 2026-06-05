"""
DB Runtime Generator.

Converts DB schema into executable SQL DDL statements
and SQLAlchemy model code.
"""

from __future__ import annotations

from src.schemas.db_schema import DBSchema, SQLDataType


def generate_db_runtime(db_schema: DBSchema) -> dict:
    """
    Convert DB schema to SQL DDL and SQLAlchemy models.

    Generates:
    - CREATE EXTENSION statements
    - CREATE TYPE (ENUM) statements
    - CREATE TABLE statements
    - CREATE INDEX statements
    - SQLAlchemy model code
    - Seed data INSERT statements
    """
    extensions_sql = []
    for ext in db_schema.extensions:
        extensions_sql.append(f'CREATE EXTENSION IF NOT EXISTS "{ext}";')

    enum_sql = []
    for enum in db_schema.enums:
        values = ", ".join(f"'{v}'" for v in enum.values)
        enum_sql.append(f"CREATE TYPE {enum.name} AS ENUM ({values});")

    table_sql = []
    index_sql = []
    sqlalchemy_models = []

    for table in db_schema.tables:
        # CREATE TABLE
        create_stmt = _generate_create_table(table)
        table_sql.append(create_stmt)

        # CREATE INDEX
        for idx in table.indexes:
            idx_stmt = _generate_create_index(idx, table.name)
            index_sql.append(idx_stmt)

        # SQLAlchemy model
        sa_model = _generate_sqlalchemy_model(table)
        sqlalchemy_models.append(sa_model)

    seed_sql = []
    for seed in db_schema.seeds:
        for record in seed.records:
            columns = ", ".join(record.keys())
            values = ", ".join(_sql_value(v) for v in record.values())
            seed_sql.append(f"INSERT INTO {seed.table} ({columns}) VALUES ({values});")

    # Complete migration SQL
    full_sql = "\n".join(
        ["-- Extensions"]
        + extensions_sql
        + ["", "-- Enum Types"]
        + enum_sql
        + ["", "-- Tables"]
        + table_sql
        + ["", "-- Indexes"]
        + index_sql
        + ["", "-- Seed Data"]
        + seed_sql
    )

    return {
        "ddl": full_sql,
        "extensions": extensions_sql,
        "enums": enum_sql,
        "tables": table_sql,
        "indexes": index_sql,
        "seeds": seed_sql,
        "sqlalchemy_models": sqlalchemy_models,
    }


def _generate_create_table(table) -> str:
    """Generate CREATE TABLE statement."""
    lines = [f"CREATE TABLE IF NOT EXISTS {table.name} ("]

    col_defs = []
    for col in table.columns:
        col_def = f"    {col.name} {_sql_type(col)}"
        if col.primary_key:
            col_def += " PRIMARY KEY"
        if not col.nullable and not col.primary_key:
            col_def += " NOT NULL"
        if col.unique and not col.primary_key:
            col_def += " UNIQUE"
        if col.default:
            col_def += f" DEFAULT {col.default}"
        col_defs.append(col_def)

    # Add timestamps if enabled
    if table.timestamps:
        has_created = any(c.name == "created_at" for c in table.columns)
        has_updated = any(c.name == "updated_at" for c in table.columns)
        if not has_created:
            col_defs.append("    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")
        if not has_updated:
            col_defs.append("    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")

    # Foreign key constraints
    for fk in table.foreign_keys:
        on_delete = fk.on_delete.value if hasattr(fk.on_delete, "value") else fk.on_delete
        on_update = fk.on_update.value if hasattr(fk.on_update, "value") else fk.on_update
        col_defs.append(
            f"    CONSTRAINT fk_{table.name}_{fk.column} "
            f"FOREIGN KEY ({fk.column}) REFERENCES {fk.references_table}({fk.references_column}) "
            f"ON DELETE {on_delete} ON UPDATE {on_update}"
        )

    # Named constraints
    for con in table.constraints:
        if con.expression:
            col_defs.append(f"    CONSTRAINT {con.name} CHECK ({con.expression})")

    lines.append(",\n".join(col_defs))
    lines.append(");")

    return "\n".join(lines)


def _generate_create_index(idx, table_name: str) -> str:
    """Generate CREATE INDEX statement."""
    unique = "UNIQUE " if idx.unique else ""
    columns = ", ".join(idx.columns)
    idx_type = idx.index_type.value if hasattr(idx.index_type, "value") else idx.index_type
    stmt = f"CREATE {unique}INDEX IF NOT EXISTS {idx.name} ON {table_name} USING {idx_type} ({columns})"
    if idx.condition:
        stmt += f" WHERE {idx.condition}"
    stmt += ";"
    return stmt


def _generate_sqlalchemy_model(table) -> str:
    """Generate SQLAlchemy model code."""
    class_name = table.entity or table.name.title().replace("_", "")
    lines = [
        f"class {class_name}(Base):",
        f'    __tablename__ = "{table.name}"',
        "",
    ]

    for col in table.columns:
        sa_type = _sqlalchemy_type(col)
        extras = []
        if col.primary_key:
            extras.append("primary_key=True")
        if not col.nullable and not col.primary_key:
            extras.append("nullable=False")
        if col.unique and not col.primary_key:
            extras.append("unique=True")
        if col.default:
            if col.default.startswith("uuid_generate"):
                extras.append("default=uuid4")
            elif col.default == "NOW()":
                extras.append("server_default=func.now()")
            else:
                extras.append(f'server_default="{col.default}"')

        extras_str = ", ".join(extras)
        if extras_str:
            lines.append(f"    {col.name} = Column({sa_type}, {extras_str})")
        else:
            lines.append(f"    {col.name} = Column({sa_type})")

    # Add relationships for FKs
    for fk in table.foreign_keys:
        ref_model = fk.references_table.title().replace("_", "")
        rel_name = fk.column.replace("_id", "")
        lines.append(
            f'    {rel_name} = relationship("{ref_model}", backref="{table.name}")'
        )

    return "\n".join(lines)


def _sql_type(col) -> str:
    """Convert column to SQL type string."""
    dt = col.data_type.value if hasattr(col.data_type, "value") else col.data_type
    if dt == "VARCHAR" and col.length:
        return f"VARCHAR({col.length})"
    if dt == "DECIMAL" and col.precision:
        scale = col.scale or 2
        return f"DECIMAL({col.precision}, {scale})"
    return dt


def _sqlalchemy_type(col) -> str:
    """Convert column to SQLAlchemy type string."""
    dt = col.data_type.value if hasattr(col.data_type, "value") else col.data_type
    mapping = {
        "UUID": "UUID(as_uuid=True)",
        "SERIAL": "Integer",
        "BIGSERIAL": "BigInteger",
        "VARCHAR": f"String({col.length or 255})",
        "TEXT": "Text",
        "INTEGER": "Integer",
        "BIGINT": "BigInteger",
        "FLOAT": "Float",
        "DECIMAL": f"Numeric({col.precision or 10}, {col.scale or 2})",
        "BOOLEAN": "Boolean",
        "DATE": "Date",
        "TIMESTAMP": "DateTime",
        "TIMESTAMPTZ": "DateTime(timezone=True)",
        "JSON": "JSON",
        "JSONB": "JSONB",
        "BYTEA": "LargeBinary",
        "ENUM": f"Enum({', '.join(repr(v) for v in col.enum_values)}, name='{col.name}_enum')" if col.enum_values else "String(50)",
    }
    return mapping.get(dt, "String(255)")


def _sql_value(v) -> str:
    """Convert Python value to SQL literal."""
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(v)
    return f"'{str(v)}'"
