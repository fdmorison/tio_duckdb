import pytest
from tiozin.api.metadata.schema.exceptions import SchemaError

from tio_duckdb.registries.schema.converters.reader import DuckdbSchemaReader


def test_read_should_read_column_as_property():
    # Arrange
    columns = {"id": "BIGINT"}

    # Act
    result = DuckdbSchemaReader().read(columns)

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


def test_read_should_read_columns_in_written_order():
    # Arrange
    columns = {"name": "VARCHAR", "id": "BIGINT", "active": "BOOLEAN"}

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = [property.name for property in result.properties]
    expected = ["name", "id", "active"]
    assert actual == expected


def test_read_should_read_no_columns_as_schema_without_properties():
    # Arrange
    columns = {}

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {"properties": []}
    assert actual == expected


@pytest.mark.parametrize(
    "duckdb_type, expected",
    [
        ("BOOLEAN", "boolean"),
        ("TINYINT", "integer"),
        ("SMALLINT", "integer"),
        ("INTEGER", "integer"),
        ("BIGINT", "integer"),
        ("HUGEINT", "integer"),
        ("UTINYINT", "integer"),
        ("USMALLINT", "integer"),
        ("UINTEGER", "integer"),
        ("UBIGINT", "integer"),
        ("UHUGEINT", "integer"),
        ("FLOAT", "number"),
        ("DOUBLE", "number"),
        ("DECIMAL(10,2)", "number"),
        ("VARCHAR", "string"),
        ("UUID", "string"),
        ("BLOB", "string"),
        ("DATE", "date"),
        ("TIME", "time"),
        ("TIMESTAMP", "timestamp"),
        ("TIMESTAMP_MS", "timestamp"),
        ("TIMESTAMP_NS", "timestamp"),
        ("TIMESTAMP WITH TIME ZONE", "timestamp"),
        ("STRUCT(id BIGINT)", "object"),
        ("VARCHAR[]", "array"),
        ("VARCHAR[3]", "array"),
        ("MAP(VARCHAR, BIGINT)", "map"),
    ],
)
def test_read_should_map_duckdb_type_to_logical_type(duckdb_type, expected):
    # Arrange
    columns = {"field": duckdb_type}

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = result["field"].logicalType
    assert actual == expected


@pytest.mark.parametrize(
    "duckdb_type, expected",
    [
        ("BOOL", "boolean"),
        ("LOGICAL", "boolean"),
        ("INT", "integer"),
        ("INT4", "integer"),
        ("SIGNED", "integer"),
        ("LONG", "integer"),
        ("REAL", "number"),
        ("NUMERIC(10,2)", "number"),
        ("TEXT", "string"),
        ("STRING", "string"),
        ("JSON", "string"),
        ("BYTEA", "string"),
        ("DATETIME", "timestamp"),
        ("TIMESTAMPTZ", "timestamp"),
    ],
)
def test_read_should_resolve_duckdb_type_aliases(duckdb_type, expected):
    # Arrange
    columns = {"field": duckdb_type}

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = result["field"].logicalType
    assert actual == expected


@pytest.mark.parametrize(
    "duckdb_type, expected",
    [
        ("bigint", "integer"),
        ("Varchar", "string"),
        ("decimal(10,2)", "number"),
        ("timestamp with time zone", "timestamp"),
    ],
)
def test_read_should_read_duckdb_type_in_any_case(duckdb_type, expected):
    # Arrange
    columns = {"field": duckdb_type}

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = result["field"].logicalType
    assert actual == expected


@pytest.mark.parametrize(
    "duckdb_type, expected",
    [
        ("decimal(10,2)", "decimal(10,2)"),
        ("INT", "INT"),
        ("TIMESTAMPTZ", "TIMESTAMPTZ"),
        ("MAP(VARCHAR, INTEGER[])", "MAP(VARCHAR, INTEGER[])"),
    ],
)
def test_read_should_keep_duckdb_type_as_written_in_physical_type(duckdb_type, expected):
    # Arrange
    columns = {"field": duckdb_type}

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = result["field"].physicalType
    assert actual == expected


@pytest.mark.parametrize(
    "duckdb_type, expected",
    [
        ("TINYINT", "i8"),
        ("SMALLINT", "i16"),
        ("INTEGER", "i32"),
        ("BIGINT", "i64"),
        ("HUGEINT", "i128"),
        ("UTINYINT", "u8"),
        ("USMALLINT", "u16"),
        ("UINTEGER", "u32"),
        ("UBIGINT", "u64"),
        ("UHUGEINT", "u128"),
        ("FLOAT", "f32"),
        ("DOUBLE", "f64"),
    ],
)
def test_read_should_read_numeric_size_as_format(duckdb_type, expected):
    # Arrange
    columns = {"field": duckdb_type}

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = result["field"].logicalTypeOptions.format
    assert actual == expected


@pytest.mark.parametrize(
    "duckdb_type, expected_precision, expected_scale",
    [
        ("DECIMAL(10,2)", 10, 2),
        ("DECIMAL(38, 10)", 38, 10),
        ("DECIMAL(10)", 10, 0),
        ("DECIMAL", 18, 3),
    ],
)
def test_read_should_read_decimal_digits_as_precision_and_scale(
    duckdb_type, expected_precision, expected_scale
):
    # Arrange
    columns = {"total": duckdb_type}

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = (
        result["total"].precision,
        result["total"].scale,
    )
    expected = (
        expected_precision,
        expected_scale,
    )
    assert actual == expected


def test_read_should_read_uuid_as_string_with_uuid_format():
    # Arrange
    columns = {"id": "UUID"}

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "id",
                "logicalType": "string",
                "physicalType": "UUID",
                "logicalTypeOptions": {"format": "uuid"},
            }
        ],
    }
    assert actual == expected


def test_read_should_read_blob_as_binary_string():
    # Arrange
    columns = {"payload": "BLOB"}

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "payload",
                "logicalType": "string",
                "physicalType": "BLOB",
                "customProperties": [{"property": "binary", "value": True}],
            }
        ],
    }
    assert actual == expected


def test_read_should_read_time_in_micros():
    # Arrange
    columns = {"starts_at": "TIME"}

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "starts_at",
                "logicalType": "time",
                "physicalType": "TIME",
                "customProperties": [{"property": "timeUnit", "value": "micros"}],
            }
        ],
    }
    assert actual == expected


@pytest.mark.parametrize(
    "duckdb_type, expected",
    [
        ("TIMESTAMP_MS", "millis"),
        ("TIMESTAMP", "micros"),
        ("TIMESTAMP_US", "micros"),
        ("DATETIME", "micros"),
        ("TIMESTAMP_NS", "nanos"),
    ],
)
def test_read_should_read_timestamp_without_timezone_in_its_unit(duckdb_type, expected):
    # Arrange
    columns = {"created_at": duckdb_type}

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = (
        result["created_at"].logicalTypeOptions.model_dump(exclude_unset=True),
        result["created_at"].timeUnit,
    )
    expected = (
        {"timezone": False},
        expected,
    )
    assert actual == expected


@pytest.mark.parametrize(
    "duckdb_type",
    [
        "TIMESTAMP WITH TIME ZONE",
        "TIMESTAMPTZ",
    ],
)
def test_read_should_read_timestamp_with_time_zone_in_micros(duckdb_type):
    # Arrange
    columns = {"created_at": duckdb_type}

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = result["created_at"].model_dump(exclude_unset=True, exclude={"physicalType"})
    expected = {
        "name": "created_at",
        "logicalType": "timestamp",
        "customProperties": [{"property": "timeUnit", "value": "micros"}],
    }
    assert actual == expected


def test_read_should_read_struct_as_object():
    # Arrange
    columns = {"address": "STRUCT(city VARCHAR, number INTEGER)"}

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "address",
                "logicalType": "object",
                "physicalType": "STRUCT(city VARCHAR, number INTEGER)",
                "properties": [
                    {"name": "city", "logicalType": "string", "physicalType": "VARCHAR"},
                    {
                        "name": "number",
                        "logicalType": "integer",
                        "physicalType": "INTEGER",
                        "logicalTypeOptions": {"format": "i32"},
                    },
                ],
            }
        ],
    }
    assert actual == expected


@pytest.mark.parametrize(
    "duckdb_type, expected",
    [
        ('STRUCT("first name" VARCHAR)', ["first name"]),
        ('STRUCT("Id" BIGINT)', ["Id"]),
        ('STRUCT("a,b" VARCHAR, c VARCHAR)', ["a,b", "c"]),
        ('STRUCT("say ""hi""" VARCHAR)', ['say "hi"']),
    ],
)
def test_read_should_unquote_struct_field_names(duckdb_type, expected):
    # Arrange
    columns = {"person": duckdb_type}

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = [property.name for property in result["person"].properties]
    assert actual == expected


def test_read_should_split_struct_fields_only_at_top_level_commas():
    # Arrange
    columns = {
        "order": "STRUCT(total DECIMAL(10,2), lines MAP(VARCHAR, INTEGER), "
        "address STRUCT(city VARCHAR, zip VARCHAR))"
    }

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = [property.name for property in result["order"].properties]
    expected = ["total", "lines", "address"]
    assert actual == expected


def test_read_should_read_list_as_array():
    # Arrange
    columns = {"tags": "VARCHAR[]"}

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "tags",
                "logicalType": "array",
                "physicalType": "VARCHAR[]",
                "items": {"logicalType": "string", "physicalType": "VARCHAR"},
            }
        ],
    }
    assert actual == expected


def test_read_should_read_fixed_size_array_as_array_with_exact_item_count():
    # Arrange
    columns = {"rgb": "INTEGER[3]"}

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "rgb",
                "logicalType": "array",
                "physicalType": "INTEGER[3]",
                "logicalTypeOptions": {"minItems": 3, "maxItems": 3},
                "items": {
                    "logicalType": "integer",
                    "physicalType": "INTEGER",
                    "logicalTypeOptions": {"format": "i32"},
                },
            }
        ],
    }
    assert actual == expected


def test_read_should_read_list_of_fixed_size_arrays_as_nested_arrays():
    # Arrange
    columns = {"points": "INTEGER[2][]"}

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "points",
                "logicalType": "array",
                "physicalType": "INTEGER[2][]",
                "items": {
                    "logicalType": "array",
                    "physicalType": "INTEGER[2]",
                    "logicalTypeOptions": {"minItems": 2, "maxItems": 2},
                    "items": {
                        "logicalType": "integer",
                        "physicalType": "INTEGER",
                        "logicalTypeOptions": {"format": "i32"},
                    },
                },
            }
        ],
    }
    assert actual == expected


def test_read_should_read_map_with_key_and_value_types():
    # Arrange
    columns = {"scores": "MAP(VARCHAR, BIGINT)"}

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "scores",
                "logicalType": "map",
                "physicalType": "MAP(VARCHAR, BIGINT)",
                "map": {
                    "key": {"logicalType": "string", "physicalType": "VARCHAR"},
                    "value": {
                        "logicalType": "integer",
                        "physicalType": "BIGINT",
                        "logicalTypeOptions": {"format": "i64"},
                    },
                },
            }
        ],
    }
    assert actual == expected


def test_read_should_read_list_of_structs_as_array_of_objects():
    # Arrange
    columns = {"lines": "STRUCT(sku VARCHAR, qty INTEGER)[]"}

    # Act
    result = DuckdbSchemaReader().read(columns)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "lines",
                "logicalType": "array",
                "physicalType": "STRUCT(sku VARCHAR, qty INTEGER)[]",
                "items": {
                    "logicalType": "object",
                    "physicalType": "STRUCT(sku VARCHAR, qty INTEGER)",
                    "properties": [
                        {"name": "sku", "logicalType": "string", "physicalType": "VARCHAR"},
                        {
                            "name": "qty",
                            "logicalType": "integer",
                            "physicalType": "INTEGER",
                            "logicalTypeOptions": {"format": "i32"},
                        },
                    ],
                },
            }
        ],
    }
    assert actual == expected


@pytest.mark.parametrize(
    "duckdb_type",
    [
        "INTERVAL",
        "BIT",
        "UNION(num INTEGER, text VARCHAR)",
        "ENUM('a', 'b')",
    ],
)
def test_read_should_raise_schema_error_when_duckdb_type_is_unsupported(duckdb_type):
    # Arrange
    columns = {"field": duckdb_type}

    # Act / Assert
    with pytest.raises(SchemaError, match="Unsupported DuckDB type"):
        DuckdbSchemaReader().read(columns)


def test_read_should_raise_schema_error_when_nested_type_is_unsupported():
    # Arrange
    columns = {"durations": "INTERVAL[]"}

    # Act / Assert
    with pytest.raises(SchemaError, match="Unsupported DuckDB type `INTERVAL`"):
        DuckdbSchemaReader().read(columns)


def test_read_should_raise_schema_error_when_struct_field_has_no_type():
    # Arrange
    columns = {"person": "STRUCT(name)"}

    # Act / Assert
    with pytest.raises(SchemaError, match="Struct field `name` has no type"):
        DuckdbSchemaReader().read(columns)
