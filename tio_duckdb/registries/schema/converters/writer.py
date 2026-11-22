from __future__ import annotations

import re
from typing import Any

from tiozin import Schema
from tiozin.api.metadata.schema.converters import conventions as conv
from tiozin.api.metadata.schema.exceptions import SchemaError
from tiozin.api.metadata.schema.model import LogicalType, Property
from tiozin.utils import default

from . import constants as const

SIMPLE_FIELD_NAME = re.compile(r"[a-z_][a-z0-9_]*")
QUOTE = '"'


class DuckdbSchemaWriter:
    """
    Writes a Schema as DuckDB columns, a mapping of column name to DuckDB
    type, the same form that `read_csv(columns=...)` takes.

    The type comes only from the logical type, its options and the Tiozin
    conventions.

    Examples:

        ```python
        schema = Schema().int64("id").array("tags", of="string")
        DuckdbSchemaWriter().write(schema)
        # {"id": "BIGINT", "tags": "VARCHAR[]"}
        ```
    """

    def write(self, schema: Schema) -> dict[str, str]:
        return {property.name: self.write_type(property) for property in schema.properties or []}

    def write_type(self, property: Property) -> str:
        """
        The DuckDB type of the given property.

        Raises SchemaError for a property with no DuckDB type, such as a
        vector, or an integer size other than i8 to i64 and u8 to u32.

        Examples:

            ```python
            DuckdbSchemaWriter().write_type(Property(name="id", logicalType="integer"))
            # "BIGINT"
            ```
        """
        match property:
            case Property(logicalType=LogicalType.STRING, binary=True):
                return const.DUCKDB_BLOB_TYPE
            case Property(logicalType=LogicalType.STRING):
                is_uuid = self.option_value(property, "format") == conv.UUID_FORMAT
                return const.DUCKDB_UUID_TYPE if is_uuid else const.DUCKDB_VARCHAR_TYPE
            case Property(logicalType=LogicalType.INTEGER):
                return self.type_by_format(
                    property,
                    const.DUCKDB_INTEGER_BY_FORMAT,
                    conv.DEFAULT_INTEGER_FORMAT,
                )
            case Property(logicalType=LogicalType.NUMBER, precision=int() as precision):
                return f"{const.DUCKDB_DECIMAL_TYPE}({precision},{default(property.scale, 0)})"
            case Property(logicalType=LogicalType.NUMBER):
                return self.type_by_format(
                    property,
                    const.DUCKDB_NUMBER_BY_FORMAT,
                    conv.DEFAULT_NUMBER_FORMAT,
                )
            case Property(logicalType=LogicalType.BOOLEAN):
                return const.DUCKDB_BOOLEAN_TYPE
            case Property(logicalType=LogicalType.DATE):
                return const.DUCKDB_DATE_TYPE
            case Property(logicalType=LogicalType.TIME):
                return const.DUCKDB_TIME_TYPE
            case Property(logicalType=LogicalType.TIMESTAMP):
                if self.option_value(property, "timezone") is False:
                    unit = default(property.timeUnit, conv.DEFAULT_TIME_UNIT)
                    return const.DUCKDB_TIMESTAMP_BY_UNIT[unit]
                return const.DUCKDB_TIMESTAMP_TZ_TYPE
            case Property(logicalType=LogicalType.OBJECT):
                fields = ", ".join(
                    f"{self.field_name(child.name)} {self.write_type(child)}"
                    for child in property.properties or []
                )
                return f"{const.DUCKDB_STRUCT_TYPE}({fields})"
            case Property(logicalType=LogicalType.ARRAY):
                min_items = self.option_value(property, "minItems")
                max_items = self.option_value(property, "maxItems")
                size = max_items if min_items is not None and min_items == max_items else ""
                return f"{self.write_type(property.items)}[{size}]"
            case Property(logicalType=LogicalType.MAP):
                key = self.write_type(property.map.key)
                value = self.write_type(property.map.value)
                return f"{const.DUCKDB_MAP_TYPE}({key}, {value})"
            case _:
                raise SchemaError(f"Logical type `{property.logicalType}` has no DuckDB type")

    def type_by_format(self, property: Property, types: dict[str, str], default_format: str) -> str:
        """
        The DuckDB type for the `format` option of the property, or for the
        default format when the option is not set.

        Raises SchemaError when no DuckDB type has that format.
        """
        size_format = default(self.option_value(property, "format"), default_format)

        SchemaError.raise_if_not_in(
            size_format,
            types,
        )

        return types[size_format]

    @staticmethod
    def field_name(name: str) -> str:
        """
        The name of a struct field as DuckDB writes it, quoted unless it is a
        simple lower case identifier.

        Examples:

            ```python
            DuckdbSchemaWriter.field_name("id")  # "id"
            DuckdbSchemaWriter.field_name("first name")  # '"first name"'
            ```
        """
        if SIMPLE_FIELD_NAME.fullmatch(name):
            return name

        return QUOTE + name.replace(QUOTE, QUOTE * 2) + QUOTE

    @staticmethod
    def option_value(property: Property, name: str) -> Any:
        """
        The value of the logical type option with the given name, or None when
        the option is not set.
        """
        options = property.logicalTypeOptions

        if options is None or name not in options.model_fields_set:
            return None

        return getattr(options, name)
