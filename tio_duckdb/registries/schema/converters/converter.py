from __future__ import annotations

import json

from tiozin import Schema
from tiozin.api.metadata.schema.converters import SchemaConverter

from .reader import DuckdbSchemaReader
from .writer import DuckdbSchemaWriter


class DuckdbSchemaConverter(SchemaConverter[dict[str, str]]):
    """
    Converts to and from DuckDB columns, a mapping of column name to DuckDB
    type, the same form that `read_csv(columns=...)` takes. Loading also
    accepts that mapping as a JSON string.

    Examples:

        ```python
        schema = Schema.from_format("duckdb", {"id": "BIGINT", "tags": "VARCHAR[]"})

        schema.to_format("duckdb")
        # {"id": "BIGINT", "tags": "VARCHAR[]"}
        ```
    """

    format = "duckdb"

    def dump(self, schema: Schema, **options) -> dict[str, str]:
        return DuckdbSchemaWriter().write(schema)

    def load(self, schema: dict[str, str] | str, **options) -> Schema:
        columns = json.loads(schema) if isinstance(schema, str) else schema
        return DuckdbSchemaReader().read(columns)
