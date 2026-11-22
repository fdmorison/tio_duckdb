import json

import pytest
from tiozin import Schema
from tiozin.api.metadata.schema.model import Property

from tio_duckdb import DuckdbSchemaConverter


def test_load_should_read_duckdb_columns():
    # Arrange
    columns = {"id": "BIGINT"}

    # Act
    result = DuckdbSchemaConverter().load(columns)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "id",
                "logicalType": "integer",
                "physicalType": "BIGINT",
                "logicalTypeOptions": {"format": "i64"},
            }
        ],
    }
    assert actual == expected


def test_load_should_accept_json_string():
    # Arrange
    columns = json.dumps({"id": "BIGINT"})

    # Act
    result = DuckdbSchemaConverter().load(columns)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "id",
                "logicalType": "integer",
                "physicalType": "BIGINT",
                "logicalTypeOptions": {"format": "i64"},
            }
        ],
    }
    assert actual == expected


def test_load_should_serve_schema_from_duckdb_format():
    # Arrange
    columns = {"id": "BIGINT"}

    # Act
    result = Schema.from_format("duckdb", columns)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "id",
                "logicalType": "integer",
                "physicalType": "BIGINT",
                "logicalTypeOptions": {"format": "i64"},
            }
        ],
    }
    assert actual == expected


def test_dump_should_write_duckdb_columns():
    # Arrange
    schema = Schema(name="users").int64("id").array("tags", of="string")

    # Act
    result = DuckdbSchemaConverter().dump(schema)

    # Assert
    actual = result
    expected = {"id": "BIGINT", "tags": "VARCHAR[]"}
    assert actual == expected


def test_dump_should_serve_schema_to_duckdb_format():
    # Arrange
    schema = Schema(name="users").int64("id").array("tags", of="string")

    # Act
    result = schema.to_format("duckdb")

    # Assert
    actual = result
    expected = {"id": "BIGINT", "tags": "VARCHAR[]"}
    assert actual == expected


@pytest.mark.parametrize(
    "columns",
    [
        {
            "active": "BOOLEAN",
            "tiny": "TINYINT",
            "small": "SMALLINT",
            "medium": "INTEGER",
            "big": "BIGINT",
            "utiny": "UTINYINT",
            "usmall": "USMALLINT",
            "umedium": "UINTEGER",
            "ratio": "FLOAT",
            "amount": "DOUBLE",
        },
        {
            "name": "VARCHAR",
            "id": "UUID",
            "payload": "BLOB",
        },
        {
            "birthday": "DATE",
            "starts_at": "TIME",
            "created_ms": "TIMESTAMP_MS",
            "created_us": "TIMESTAMP",
            "created_ns": "TIMESTAMP_NS",
            "created_tz": "TIMESTAMP WITH TIME ZONE",
        },
        {
            "price": "DECIMAL(10,2)",
            "total": "DECIMAL(38,10)",
            "count": "DECIMAL(10,0)",
            "default": "DECIMAL(18,3)",
        },
        {
            "address": "STRUCT(city VARCHAR, zip VARCHAR)",
            "person": 'STRUCT("first name" VARCHAR, "Last Name" VARCHAR, "say ""hi""" VARCHAR)',
            "order": "STRUCT(id BIGINT, customer STRUCT(id BIGINT, name VARCHAR))",
        },
        {
            "tags": "VARCHAR[]",
            "matrix": "INTEGER[][]",
            "lines": "STRUCT(sku VARCHAR, qty INTEGER)[]",
        },
        {
            "rgb": "INTEGER[3]",
            "points": "DOUBLE[2][]",
            "grid": "TINYINT[3][3]",
        },
        {
            "scores": "MAP(VARCHAR, BIGINT)",
            "prices": "MAP(VARCHAR, DECIMAL(10,2))",
            "nested": "MAP(INTEGER, MAP(VARCHAR, VARCHAR[]))",
            "profiles": "MAP(VARCHAR, STRUCT(name VARCHAR, tags VARCHAR[]))",
        },
    ],
    ids=[
        "booleans_and_numbers",
        "strings",
        "dates_and_times",
        "decimals",
        "structs",
        "lists",
        "arrays",
        "maps",
    ],
)
def test_load_should_round_trip_duckdb_columns(columns):
    # Act
    result = DuckdbSchemaConverter().dump(DuckdbSchemaConverter().load(columns))

    # Assert
    actual = result
    expected = columns
    assert actual == expected


@pytest.mark.parametrize(
    "duckdb_type, expected",
    [
        ("INT", "INTEGER"),
        ("bigint", "BIGINT"),
        ("TEXT", "VARCHAR"),
        ("NUMERIC(10,2)", "DECIMAL(10,2)"),
        ("DECIMAL", "DECIMAL(18,3)"),
        ("DECIMAL(10)", "DECIMAL(10,0)"),
        ("DATETIME", "TIMESTAMP"),
        ("TIMESTAMPTZ", "TIMESTAMP WITH TIME ZONE"),
        ("MAP(TEXT, INT)", "MAP(VARCHAR, INTEGER)"),
        ("STRUCT(Id INT)", 'STRUCT("Id" INTEGER)'),
    ],
)
def test_load_should_round_trip_duckdb_type_to_its_canonical_spelling(duckdb_type, expected):
    # Arrange
    columns = {"field": duckdb_type}

    # Act
    result = DuckdbSchemaConverter().dump(DuckdbSchemaConverter().load(columns))

    # Assert
    actual = result["field"]
    assert actual == expected


def test_load_should_restore_dumped_schema():
    # Arrange
    schema = Schema(
        name="orders",
        properties=[
            Property(name="id", logicalType="integer"),
            Property(
                name="total",
                logicalType="number",
                customProperties=[
                    {"property": "precision", "value": 10},
                    {"property": "scale", "value": 2},
                ],
            ),
            Property(
                name="tags",
                logicalType="array",
                items=Property(logicalType="string"),
            ),
        ],
    )

    # Act
    result = DuckdbSchemaConverter().load(DuckdbSchemaConverter().dump(schema))

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "id",
                "logicalType": "integer",
                "physicalType": "BIGINT",
                "logicalTypeOptions": {"format": "i64"},
            },
            {
                "name": "total",
                "logicalType": "number",
                "physicalType": "DECIMAL(10,2)",
                "customProperties": [
                    {"property": "precision", "value": 10},
                    {"property": "scale", "value": 2},
                ],
            },
            {
                "name": "tags",
                "logicalType": "array",
                "physicalType": "VARCHAR[]",
                "items": {"logicalType": "string", "physicalType": "VARCHAR"},
            },
        ],
    }
    assert actual == expected
