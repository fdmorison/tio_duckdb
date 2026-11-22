from __future__ import annotations

from typing import Any

from tiozin import Schema
from tiozin.api.metadata.schema.converters import conventions as conv
from tiozin.api.metadata.schema.exceptions import SchemaError
from tiozin.api.metadata.schema.model import LogicalType, Property

from . import constants as const
from .duckdb_type import DuckdbType


class DuckdbSchemaReader:
    """
    Reads DuckDB columns, a mapping of column name to DuckDB type, into a
    Schema.

    DuckDB columns carry no comments or nullability, so the schema has only
    names and types.

    Examples:

        ```python
        DuckdbSchemaReader().read({"id": "BIGINT", "tags": "VARCHAR[]"})
        # Schema(properties=[
        #     Property(name="id", logicalType="integer", physicalType="BIGINT", ...),
        #     Property(name="tags", logicalType="array", physicalType="VARCHAR[]", ...),
        # ])
        ```
    """

    def read(self, columns: dict[str, str]) -> Schema:
        return Schema(
            properties=[
                self.read_type(DuckdbType(type_name), {"name": name})
                for name, type_name in columns.items()
            ]
        )

    def read_type(self, duckdb_type: DuckdbType, attributes: dict[str, Any]) -> Property:
        """
        Builds a property of the given DuckDB type with the given attributes.

        Raises SchemaError for a DuckDB type with no logical type, such as
        INTERVAL or UNION.

        Examples:

            ```python
            DuckdbSchemaReader().read_type(DuckdbType("DECIMAL(10,2)"), {"name": "total"})
            # Property(name="total", logicalType="number", physicalType="DECIMAL(10,2)",
            #          precision=10, scale=2)
            ```
        """
        attributes = {**attributes, "physicalType": duckdb_type.physical_type}

        match duckdb_type.type_name:
            case const.DUCKDB_BOOLEAN_TYPE:
                return Property(logicalType=LogicalType.BOOLEAN, **attributes)
            case type_name if type_name in const.DUCKDB_INTEGER_FORMATS:
                return Property(
                    logicalType=LogicalType.INTEGER,
                    logicalTypeOptions={"format": const.DUCKDB_INTEGER_FORMATS[type_name]},
                    **attributes,
                )
            case type_name if type_name in const.DUCKDB_NUMBER_FORMATS:
                return Property(
                    logicalType=LogicalType.NUMBER,
                    logicalTypeOptions={"format": const.DUCKDB_NUMBER_FORMATS[type_name]},
                    **attributes,
                )
            case const.DUCKDB_DECIMAL_TYPE:
                return Property(
                    logicalType=LogicalType.NUMBER,
                    precision=duckdb_type.precision,
                    scale=duckdb_type.scale,
                    **attributes,
                )
            case const.DUCKDB_VARCHAR_TYPE:
                return Property(logicalType=LogicalType.STRING, **attributes)
            case const.DUCKDB_UUID_TYPE:
                return Property(
                    logicalType=LogicalType.STRING,
                    logicalTypeOptions={"format": conv.UUID_FORMAT},
                    **attributes,
                )
            case const.DUCKDB_BLOB_TYPE:
                return Property(logicalType=LogicalType.STRING, binary=True, **attributes)
            case const.DUCKDB_DATE_TYPE:
                return Property(logicalType=LogicalType.DATE, **attributes)
            case const.DUCKDB_TIME_TYPE:
                return Property(logicalType=LogicalType.TIME, timeUnit=conv.MICROS, **attributes)
            case type_name if type_name in const.DUCKDB_TIMESTAMP_UNITS:
                return Property(
                    logicalType=LogicalType.TIMESTAMP,
                    logicalTypeOptions={"timezone": False},
                    timeUnit=const.DUCKDB_TIMESTAMP_UNITS[type_name],
                    **attributes,
                )
            case const.DUCKDB_TIMESTAMP_TZ_TYPE:
                return Property(
                    logicalType=LogicalType.TIMESTAMP,
                    timeUnit=conv.MICROS,
                    **attributes,
                )
            case const.DUCKDB_STRUCT_TYPE:
                return Property(
                    logicalType=LogicalType.OBJECT,
                    properties=[
                        self.read_type(field_type, {"name": name})
                        for name, field_type in duckdb_type.fields
                    ],
                    **attributes,
                )
            case const.DUCKDB_LIST_TYPE:
                return Property(
                    logicalType=LogicalType.ARRAY,
                    items=self.read_type(duckdb_type.element_type, {}),
                    **attributes,
                )
            case const.DUCKDB_ARRAY_TYPE:
                return Property(
                    logicalType=LogicalType.ARRAY,
                    logicalTypeOptions={
                        "minItems": duckdb_type.array_size,
                        "maxItems": duckdb_type.array_size,
                    },
                    items=self.read_type(duckdb_type.element_type, {}),
                    **attributes,
                )
            case const.DUCKDB_MAP_TYPE:
                return Property(
                    logicalType=LogicalType.MAP,
                    map={
                        "key": self.read_type(duckdb_type.key_type, {}),
                        "value": self.read_type(duckdb_type.value_type, {}),
                    },
                    **attributes,
                )
            case _:
                raise SchemaError(f"Unsupported DuckDB type `{duckdb_type.physical_type}`")
