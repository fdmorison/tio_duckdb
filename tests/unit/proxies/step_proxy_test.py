from pathlib import Path

from duckdb import DuckDBPyConnection
from tiozin import Context, Schema
from tiozin.api.metadata.bundle import Registries
from tiozin.family.tio_kernel import FileSchemaRegistry

from tests.stubs import JobStub
from tio_duckdb import (
    DuckdbFileInput,
    DuckdbFileOutput,
    DuckdbSqlTransform,
    DuckdbWordCountTransform,
)

# =============================================================================
# Testing DuckdbStepProxy._register_view — name as view name
# =============================================================================


def test_proxy_should_register_view_using_step_name(duckdb_session: DuckDBPyConnection):
    """View is registered under the normalized step name."""
    # Arrange
    step = DuckdbWordCountTransform(name="my word count step")
    relation = duckdb_session.sql("SELECT 'hello world' AS value").set_alias("raw_input")
    duckdb_session.register("raw_input", relation)

    # Act
    result = step.transform(relation)

    # Assert
    actual = result.alias
    expected = "my_word_count_step"
    assert actual == expected


def test_proxy_should_make_view_queryable_by_name(duckdb_session: DuckDBPyConnection):
    """After registration, the view is accessible by its name in SQL."""
    # Arrange
    step = DuckdbWordCountTransform(name="my word count step")
    relation = duckdb_session.sql("SELECT 'hello world' AS value").set_alias("raw_input")
    duckdb_session.register("raw_input", relation)

    # Act
    step.transform(relation)

    # Assert — name is a valid SQL identifier and the view is queryable
    actual = duckdb_session.sql("SELECT * FROM my_word_count_step").fetchall()
    assert len(actual) > 0


def test_proxy_should_normalize_view_name_when_name_has_special_characters(
    duckdb_session: DuckDBPyConnection,
):
    """The view name handles hyphens, mixed case, and extra spaces in the step name."""
    # Arrange
    step = DuckdbWordCountTransform(name="Word Count - 2024!")
    relation = duckdb_session.sql("SELECT 'hello world' AS value").set_alias("raw_input")
    duckdb_session.register("raw_input", relation)

    # Act
    result = step.transform(relation)

    # Assert
    actual = result.alias
    expected = "word_count_2024"
    assert actual == expected


# =============================================================================
# Testing DuckdbStepProxy — output schema observed from the relation
# =============================================================================


def test_transform_should_record_relation_schema_as_output_schema(
    duckdb_session: DuckDBPyConnection,
):
    # Arrange
    relation = duckdb_session.sql("SELECT 'hello world' AS value").set_alias("raw_input")
    duckdb_session.register("raw_input", relation)

    # Act
    step = DuckdbWordCountTransform(name="word_count")
    result = step.transform(relation)

    # Assert
    actual = result.tiozin_schema.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {"name": "word", "logicalType": "string", "physicalType": "VARCHAR"},
            {
                "name": "count",
                "logicalType": "integer",
                "physicalType": "BIGINT",
                "logicalTypeOptions": {"format": "i64"},
            },
        ],
    }
    assert actual == expected


def test_transform_should_record_nested_column_types_in_output_schema(
    duckdb_session: DuckDBPyConnection,
):
    # Arrange
    relation = duckdb_session.sql("SELECT 1 AS id").set_alias("raw_sales")
    duckdb_session.register("raw_sales", relation)

    # Act
    step = DuckdbSqlTransform(
        name="sales_summary",
        query="""
            SELECT
                id,
                12.5::DECIMAL(10,2) AS total,
                {'first name': 'alice', 'age': 30} AS customer,
                ['books', 'games'] AS tags,
                [255, 0, 0]::INTEGER[3] AS rgb,
                MAP {'books': 2} AS quantities,
                '2026-01-16 10:00:00'::TIMESTAMP AS created_at
            FROM @data
        """,
    )
    result = step.transform(relation)

    # Assert
    actual = result.tiozin_schema.to_format("duckdb")
    expected = {
        "id": "INTEGER",
        "total": "DECIMAL(10,2)",
        "customer": 'STRUCT("first name" VARCHAR, age INTEGER)',
        "tags": "VARCHAR[]",
        "rgb": "INTEGER[3]",
        "quantities": "MAP(VARCHAR, INTEGER)",
        "created_at": "TIMESTAMP",
    }
    assert actual == expected


def test_read_should_record_relation_schema_as_output_schema(tmp_path: Path):
    # Arrange
    source = tmp_path / "orders.csv"
    source.write_text("id,name\n1,alice\n")

    # Act
    step = DuckdbFileInput(name="orders_input", path=str(source), format="csv")
    result = step.read()

    # Assert
    actual = result.tiozin_schema.to_format("duckdb")
    expected = {"id": "BIGINT", "name": "VARCHAR"}
    assert actual == expected


def test_write_should_record_input_relation_schema_as_output_schema(
    duckdb_session: DuckDBPyConnection, tmp_path: Path
):
    # Arrange
    relation = duckdb_session.sql("SELECT 1::INTEGER AS id, 'alice' AS name")

    # Act
    step = DuckdbFileOutput(name="orders_output", path=str(tmp_path / "out"), format="csv")
    step.write(relation)

    # Assert
    outputs = Context.current().catalog.get_outputs(step)
    actual = outputs[0].tiozin_schema.to_format("duckdb")
    expected = {"id": "INTEGER", "name": "VARCHAR"}
    assert actual == expected


# =============================================================================
# Testing DuckdbStepProxy — output schema documented from the registry contract
# =============================================================================


def test_transform_should_document_output_schema_from_contract(
    duckdb_session: DuckDBPyConnection, duckdb_job_stub: JobStub, tmp_path: Path
):
    # Arrange
    registry = FileSchemaRegistry(location=str(tmp_path / "schemas"))
    registry.register(
        "word_counts",
        Schema(name="word_counts")
        .string("word", description="A word from the text.")
        .integer("count", description="Times the word appears."),
    )
    relation = duckdb_session.sql("SELECT 'hello world' AS value").set_alias("raw_input")
    duckdb_session.register("raw_input", relation)

    # Act
    with Context.for_job(duckdb_job_stub, registries=Registries(schema=registry)):
        step = DuckdbWordCountTransform(name="word_count", schema_subject="word_counts")
        result = step.transform(relation)

    # Assert
    actual = result.tiozin_schema.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "word",
                "logicalType": "string",
                "physicalType": "VARCHAR",
                "description": "A word from the text.",
            },
            {
                "name": "count",
                "logicalType": "integer",
                "physicalType": "BIGINT",
                "logicalTypeOptions": {"format": "i64"},
                "description": "Times the word appears.",
            },
        ],
    }
    assert actual == expected


def test_transform_should_leave_column_undocumented_when_contract_does_not_declare_it(
    duckdb_session: DuckDBPyConnection, duckdb_job_stub: JobStub, tmp_path: Path
):
    # Arrange
    registry = FileSchemaRegistry(location=str(tmp_path / "schemas"))
    registry.register(
        "word_counts",
        Schema(name="word_counts").string("word", description="A word from the text."),
    )
    relation = duckdb_session.sql("SELECT 'hello world' AS value").set_alias("raw_input")
    duckdb_session.register("raw_input", relation)

    # Act
    with Context.for_job(duckdb_job_stub, registries=Registries(schema=registry)):
        step = DuckdbWordCountTransform(name="word_count", schema_subject="word_counts")
        result = step.transform(relation)

    # Assert
    actual = result.tiozin_schema.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "word",
                "logicalType": "string",
                "physicalType": "VARCHAR",
                "description": "A word from the text.",
            },
            {
                "name": "count",
                "logicalType": "integer",
                "physicalType": "BIGINT",
                "logicalTypeOptions": {"format": "i64"},
            },
        ],
    }
    assert actual == expected


def test_transform_should_keep_relation_structure_when_contract_differs(
    duckdb_session: DuckDBPyConnection, duckdb_job_stub: JobStub, tmp_path: Path
):
    # Arrange
    registry = FileSchemaRegistry(location=str(tmp_path / "schemas"))
    registry.register(
        "word_counts",
        Schema(name="word_counts")
        .integer("word", description="A word from the text.")
        .string("language", description="Language of the word."),
    )
    relation = duckdb_session.sql("SELECT 'hello world' AS value").set_alias("raw_input")
    duckdb_session.register("raw_input", relation)

    # Act
    with Context.for_job(duckdb_job_stub, registries=Registries(schema=registry)):
        step = DuckdbWordCountTransform(name="word_count", schema_subject="word_counts")
        result = step.transform(relation)

    # Assert
    actual = result.tiozin_schema.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "word",
                "logicalType": "string",
                "physicalType": "VARCHAR",
                "description": "A word from the text.",
            },
            {
                "name": "count",
                "logicalType": "integer",
                "physicalType": "BIGINT",
                "logicalTypeOptions": {"format": "i64"},
            },
        ],
    }
    assert actual == expected


def test_read_should_document_output_schema_from_contract(duckdb_job_stub: JobStub, tmp_path: Path):
    # Arrange
    registry = FileSchemaRegistry(location=str(tmp_path / "schemas"))
    registry.register(
        "orders",
        Schema(name="orders").integer("id", description="Order id."),
    )
    source = tmp_path / "orders.csv"
    source.write_text("id,name\n1,alice\n")

    # Act
    with Context.for_job(duckdb_job_stub, registries=Registries(schema=registry)):
        step = DuckdbFileInput(
            name="orders_input",
            path=str(source),
            format="csv",
            schema_subject="orders",
        )
        result = step.read()

    # Assert
    actual = result.tiozin_schema.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "id",
                "logicalType": "integer",
                "physicalType": "BIGINT",
                "logicalTypeOptions": {"format": "i64"},
                "description": "Order id.",
            },
            {"name": "name", "logicalType": "string", "physicalType": "VARCHAR"},
        ],
    }
    assert actual == expected


def test_write_should_document_output_schema_from_contract(
    duckdb_session: DuckDBPyConnection, duckdb_job_stub: JobStub, tmp_path: Path
):
    # Arrange
    registry = FileSchemaRegistry(location=str(tmp_path / "schemas"))
    registry.register(
        "orders",
        Schema(name="orders")
        .integer("id", description="Order id.")
        .string("name", description="Customer name."),
    )
    relation = duckdb_session.sql("SELECT 1::INTEGER AS id, 'alice' AS name")

    # Act
    with Context.for_job(duckdb_job_stub, registries=Registries(schema=registry)) as context:
        step = DuckdbFileOutput(
            name="orders_output",
            path=str(tmp_path / "out"),
            format="csv",
            schema_subject="orders",
        )
        step.write(relation)

    # Assert
    outputs = context.catalog.get_outputs(step)
    actual = outputs[0].tiozin_schema.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "id",
                "logicalType": "integer",
                "physicalType": "INTEGER",
                "logicalTypeOptions": {"format": "i32"},
                "description": "Order id.",
            },
            {
                "name": "name",
                "logicalType": "string",
                "physicalType": "VARCHAR",
                "description": "Customer name.",
            },
        ],
    }
    assert actual == expected
