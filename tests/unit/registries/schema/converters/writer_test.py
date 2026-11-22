import pytest
from tiozin import Schema
from tiozin.api.metadata.schema.exceptions import SchemaError
from tiozin.api.metadata.schema.model import Property

from tio_duckdb.registries.schema.converters.writer import DuckdbSchemaWriter


def test_write_should_write_column_per_property():
    # Arrange
    schema = Schema(name="users").int64("id").string("name")

    # Act
    result = DuckdbSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {"id": "BIGINT", "name": "VARCHAR"}
    assert actual == expected


def test_write_should_write_no_columns_when_schema_has_no_properties():
    # Arrange
    schema = Schema(name="users")

    # Act
    result = DuckdbSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {}
    assert actual == expected


@pytest.mark.parametrize(
    "logical_type, expected",
    [
        ("boolean", "BOOLEAN"),
        ("string", "VARCHAR"),
        ("integer", "BIGINT"),
        ("number", "DOUBLE"),
        ("date", "DATE"),
        ("time", "TIME"),
        ("timestamp", "TIMESTAMP WITH TIME ZONE"),
    ],
)
def test_write_should_pick_duckdb_type_from_logical_type(logical_type, expected):
    # Arrange
    schema = Schema(name="users").add("field", logical_type)

    # Act
    result = DuckdbSchemaWriter().write(schema)

    # Assert
    actual = result["field"]
    assert actual == expected


@pytest.mark.parametrize(
    "logical_type, size_format, expected",
    [
        ("integer", "i8", "TINYINT"),
        ("integer", "i16", "SMALLINT"),
        ("integer", "i32", "INTEGER"),
        ("integer", "i64", "BIGINT"),
        ("integer", "u8", "UTINYINT"),
        ("integer", "u16", "USMALLINT"),
        ("integer", "u32", "UINTEGER"),
        ("number", "f32", "FLOAT"),
        ("number", "f64", "DOUBLE"),
    ],
)
def test_write_should_pick_duckdb_size_from_format(logical_type, size_format, expected):
    # Arrange
    schema = Schema(name="users").add(
        "field", logical_type, logicalTypeOptions={"format": size_format}
    )

    # Act
    result = DuckdbSchemaWriter().write(schema)

    # Assert
    actual = result["field"]
    assert actual == expected


def test_write_should_ignore_physical_type_when_picking_duckdb_type():
    # Arrange
    schema = Schema(name="users").integer("id", physicalType="TINYINT")

    # Act
    result = DuckdbSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {"id": "BIGINT"}
    assert actual == expected


@pytest.mark.parametrize(
    "precision, scale, expected",
    [
        (10, 2, "DECIMAL(10,2)"),
        (38, 10, "DECIMAL(38,10)"),
        (10, None, "DECIMAL(10,0)"),
    ],
)
def test_write_should_write_number_with_precision_as_decimal(precision, scale, expected):
    # Arrange
    schema = Schema(name="orders").decimal("total", precision, scale)

    # Act
    result = DuckdbSchemaWriter().write(schema)

    # Assert
    actual = result["total"]
    assert actual == expected


def test_write_should_write_uuid_string_as_uuid():
    # Arrange
    schema = Schema(name="users").uuid("id")

    # Act
    result = DuckdbSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {"id": "UUID"}
    assert actual == expected


def test_write_should_write_binary_string_as_blob():
    # Arrange
    schema = Schema(name="files").binary("payload")

    # Act
    result = DuckdbSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {"payload": "BLOB"}
    assert actual == expected


@pytest.mark.parametrize(
    "time_unit, expected",
    [
        ("millis", "TIMESTAMP_MS"),
        ("micros", "TIMESTAMP"),
        ("nanos", "TIMESTAMP_NS"),
    ],
)
def test_write_should_write_timestamp_without_timezone_in_its_unit(time_unit, expected):
    # Arrange
    schema = Schema(name="events").timestamp(
        "created_at",
        logicalTypeOptions={"timezone": False},
        timeUnit=time_unit,
    )

    # Act
    result = DuckdbSchemaWriter().write(schema)

    # Assert
    actual = result["created_at"]
    assert actual == expected


def test_write_should_write_timestamp_without_timezone_in_micros_by_default():
    # Arrange
    schema = Schema(name="events").timestamp_ntz("created_at")

    # Act
    result = DuckdbSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {"created_at": "TIMESTAMP"}
    assert actual == expected


@pytest.mark.parametrize(
    "time_unit",
    [
        "millis",
        "micros",
        "nanos",
    ],
)
def test_write_should_write_timestamp_with_timezone_of_any_unit_as_timestamptz(time_unit):
    # Arrange
    schema = Schema(name="events").timestamp("created_at", timeUnit=time_unit)

    # Act
    result = DuckdbSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {"created_at": "TIMESTAMP WITH TIME ZONE"}
    assert actual == expected


def test_write_should_write_object_as_struct():
    # Arrange
    schema = (
        Schema(name="users")
        .object("address")
        .string(["address", "city"])
        .int32(["address", "number"])
    )

    # Act
    result = DuckdbSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {"address": "STRUCT(city VARCHAR, number INTEGER)"}
    assert actual == expected


@pytest.mark.parametrize(
    "field_name, expected",
    [
        ("id", "STRUCT(id VARCHAR)"),
        ("_id2", "STRUCT(_id2 VARCHAR)"),
        ("first name", 'STRUCT("first name" VARCHAR)'),
        ("Id", 'STRUCT("Id" VARCHAR)'),
        ("2nd", 'STRUCT("2nd" VARCHAR)'),
        ('say "hi"', 'STRUCT("say ""hi""" VARCHAR)'),
    ],
)
def test_write_should_quote_struct_field_name_unless_simple_lower_case(field_name, expected):
    # Arrange
    schema = Schema(name="users").object("person").string(["person", field_name])

    # Act
    result = DuckdbSchemaWriter().write(schema)

    # Assert
    actual = result["person"]
    assert actual == expected


def test_write_should_write_array_as_list():
    # Arrange
    schema = Schema(name="posts").array("tags", of="string")

    # Act
    result = DuckdbSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {"tags": "VARCHAR[]"}
    assert actual == expected


def test_write_should_write_array_with_exact_item_count_as_fixed_size_array():
    # Arrange
    schema = Schema(name="colors").array(
        "rgb",
        of="integer",
        logicalTypeOptions={"minItems": 3, "maxItems": 3},
    )

    # Act
    result = DuckdbSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {"rgb": "BIGINT[3]"}
    assert actual == expected


@pytest.mark.parametrize(
    "logical_type_options",
    [
        {"minItems": 1, "maxItems": 3},
        {"maxItems": 3},
        {"minItems": 3},
    ],
)
def test_write_should_write_array_as_list_when_item_count_is_not_exact(logical_type_options):
    # Arrange
    schema = Schema(name="colors").array(
        "rgb",
        of="integer",
        logicalTypeOptions=logical_type_options,
    )

    # Act
    result = DuckdbSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {"rgb": "BIGINT[]"}
    assert actual == expected


def test_write_should_write_map_with_key_and_value_types():
    # Arrange
    schema = Schema(name="users").map("scores", value="integer")

    # Act
    result = DuckdbSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {"scores": "MAP(VARCHAR, BIGINT)"}
    assert actual == expected


def test_write_should_write_nested_types_inside_each_other():
    # Arrange
    schema = Schema(
        name="orders",
        properties=[
            Property(
                name="lines",
                logicalType="array",
                items=Property(
                    logicalType="object",
                    properties=[
                        Property(name="sku", logicalType="string"),
                        Property(
                            name="prices",
                            logicalType="map",
                            map={
                                "key": Property(logicalType="string"),
                                "value": Property(
                                    logicalType="number",
                                    customProperties=[
                                        {"property": "precision", "value": 10},
                                        {"property": "scale", "value": 2},
                                    ],
                                ),
                            },
                        ),
                    ],
                ),
            )
        ],
    )

    # Act
    result = DuckdbSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {"lines": "STRUCT(sku VARCHAR, prices MAP(VARCHAR, DECIMAL(10,2)))[]"}
    assert actual == expected


@pytest.mark.parametrize(
    "size_format",
    [
        "i128",
        "u64",
        "u128",
    ],
)
def test_write_should_raise_schema_error_when_duckdb_has_no_type_for_integer_format(size_format):
    # Arrange
    schema = Schema(name="users").integer("id", logicalTypeOptions={"format": size_format})

    # Act / Assert
    with pytest.raises(SchemaError):
        DuckdbSchemaWriter().write(schema)


def test_write_should_raise_schema_error_when_logical_type_has_no_duckdb_type():
    # Arrange
    schema = Schema(name="documents").add("embedding", "vector")

    # Act / Assert
    with pytest.raises(SchemaError, match="Logical type `vector` has no DuckDB type"):
        DuckdbSchemaWriter().write(schema)


def test_write_should_raise_schema_error_when_property_has_no_logical_type():
    # Arrange
    schema = Schema(name="users", properties=[Property(name="anything")])

    # Act / Assert
    with pytest.raises(SchemaError, match="Logical type `None` has no DuckDB type"):
        DuckdbSchemaWriter().write(schema)
