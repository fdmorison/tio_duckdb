# Schemas Guide

Every DuckDB step records the schema of the data it produces. Tiozin calls it the step's output schema, and [lineage](https://github.com/fdmorison/tiozin/blob/main/docs/how-to/openlineage.md#what-gets-emitted) reports its fields.

The Hamlet example jobs show how it works. After completing the setup in [Getting Started](getting-started.md), run them from the repository root:

```bash
tiozin run examples/jobs/shakespeare/ingestion_job.yaml
tiozin run examples/jobs/shakespeare/refined_hamlet_job.yaml
```

The refined job counts the words of Hamlet:

```yaml
transforms:
  - kind: DuckdbWordCountTransform
    name: count_words
    content_field: value
    lowercase: true
```

After it runs, its output schema is:

```yaml
properties:
- name: word
  logicalType: string
  physicalType: VARCHAR
- name: count
  logicalType: integer
  physicalType: BIGINT
  logicalTypeOptions:
    format: i64
```

Tiozin reads this schema from the columns and types of the step's result. Inputs and transforms record the schema of the relation they return. An output records the schema of the data it receives.

The schema follows the canonical Tiozin schema, described in [How to Use Schemas in Jobs](https://github.com/fdmorison/tiozin/blob/main/docs/how-to/schemas.md).

## Documenting the Schema with a Contract

A DuckDB column carries only a name and a type. Descriptions come from a contract: a schema the step fetches from the schema registry through `schema_subject`. See [Attach a schema to a step](https://github.com/fdmorison/tiozin/blob/main/docs/how-to/schemas.md#attach-a-schema-to-a-step) for how a step finds its contract.

The input of the refined Hamlet job declares one:

```yaml
inputs:
  - kind: DuckdbFileInput
    name: load_poems
    layer: raw
    path: .output/lake-{{domain}}-{{layer}}/{{product}}/{{product}}/date={{today}}/filestem={{model}}
    schema_subject: auto
    # → tiozin.latam.literature.classics.raw.shakespeare.hamlet
```

The contract lives in [`examples/schemas/tiozin.latam.literature.classics.raw.shakespeare.hamlet.yaml`](../examples/schemas/tiozin.latam.literature.classics.raw.shakespeare.hamlet.yaml):

```yaml
name: hamlet
physicalName: hamlet
physicalType: table
description: Raw text of Hamlet, one row per line.

properties:

  - name: value
    logicalType: string
    physicalType: string
    required: true
    description: One line of the play
```

When the step has a contract, Tiozin copies the contract's documentation onto the schema read from the data. Structure and types still come from the data, so columns the contract leaves out are kept, and constraints such as `required` are not copied. The output schema of `load_poems` is:

```yaml
description: Raw text of Hamlet, one row per line.
properties:
- name: value
  logicalType: string
  physicalType: VARCHAR
  description: One line of the play
- name: filesize
  logicalType: integer
  physicalType: BIGINT
  logicalTypeOptions:
    format: i64
# ... one property per remaining column
```

[Evolve a Schema and Copy Its Documentation](https://github.com/fdmorison/tiozin/blob/main/docs/how-to/schemas.md#evolve-a-schema-and-copy-its-documentation) lists the documentation fields Tiozin copies.

## The DuckDB Schema Format

The family adds a `duckdb` schema format. It converts a schema to and from DuckDB columns: a mapping of column name to [DuckDB type](https://duckdb.org/docs/stable/sql/data_types/overview), the same form that `read_csv(columns=...)` takes.

```python
import tio_duckdb
from tiozin import Schema

schema = Schema.from_format("duckdb", {"id": "BIGINT", "tags": "VARCHAR[]"})

schema.to_format("duckdb")
# → {"id": "BIGINT", "tags": "VARCHAR[]"}
```

Importing `tio_duckdb` registers the format. Jobs that use the family's plugins already have it.

Loading also accepts the mapping as a JSON string:

```python
schema = Schema.from_format("duckdb", '{"id": "BIGINT", "tags": "VARCHAR[]"}')
```

DuckDB columns carry no comments or nullability, so a loaded schema has only names and types.

## Type Mapping

Each DuckDB type maps to a logical type of the canonical schema:

| DuckDB type | Logical type | Details |
| ----------- | ------------ | ------- |
| `BOOLEAN` | `boolean` | |
| `TINYINT`, `SMALLINT`, `INTEGER`, `BIGINT`, `HUGEINT` | `integer` | `format` `i8`, `i16`, `i32`, `i64`, `i128` |
| `UTINYINT`, `USMALLINT`, `UINTEGER`, `UBIGINT`, `UHUGEINT` | `integer` | `format` `u8`, `u16`, `u32`, `u64`, `u128` |
| `FLOAT`, `DOUBLE` | `number` | `format` `f32`, `f64` |
| `DECIMAL(p,s)` | `number` | `precision` and `scale` |
| `VARCHAR` | `string` | |
| `UUID` | `string` | `format` `uuid` |
| `BLOB` | `string` | `binary` |
| `DATE` | `date` | |
| `TIME` | `time` | `timeUnit` `micros` |
| `TIMESTAMP_MS`, `TIMESTAMP`, `TIMESTAMP_NS` | `timestamp` | `timezone` false, `timeUnit` `millis`, `micros`, `nanos` |
| `TIMESTAMP WITH TIME ZONE` | `timestamp` | `timeUnit` `micros` |
| `STRUCT(...)` | `object` | |
| `T[]` | `array` | |
| `T[n]` | `array` | `minItems` and `maxItems` set to `n` |
| `MAP(K, V)` | `map` | |

DuckDB aliases, such as `INT`, `TEXT`, and `TIMESTAMPTZ`, load as the type they stand for.

Writing goes the other way. The DuckDB type comes only from the logical type, its options, and the Tiozin conventions such as `precision` and `binary`. When the schema leaves something out, the writer fills it in:

- An integer without `format` becomes `BIGINT`.
- A number without `format` or `precision` becomes `DOUBLE`.
- A decimal without `scale` becomes `DECIMAL(p,0)`.
- A timestamp becomes `TIMESTAMP WITH TIME ZONE`. If its `timezone` option is false, it becomes `TIMESTAMP_MS`, `TIMESTAMP`, or `TIMESTAMP_NS` by its `timeUnit`, and `TIMESTAMP` when `timeUnit` is not set.
- An array becomes `T[n]` only when `minItems` and `maxItems` are equal.

```python
schema = Schema().integer("id").number("total", precision=10, scale=2).timestamp("created_at")

schema.to_format("duckdb")
# → {"id": "BIGINT", "total": "DECIMAL(10,2)", "created_at": "TIMESTAMP WITH TIME ZONE"}
```

## Types Without a Match

Some types have no counterpart on the other side, and the conversion raises `SchemaError`:

- Loading a DuckDB type with no logical type, such as `INTERVAL` or `UNION`.
- Writing a property with no DuckDB type, such as a vector, or an integer whose `format` is not one of `i8` to `i64` or `u8` to `u32`.

Steps read their output schema with the same conversion. If a step returns a column of a type with no logical type, such as `INTERVAL`, the step fails with that error.

## Next Steps

- [How to Use Schemas in Jobs](https://github.com/fdmorison/tiozin/blob/main/docs/how-to/schemas.md): schema registries, subjects, and the canonical schema.
- [How to Configure OpenLineage](https://github.com/fdmorison/tiozin/blob/main/docs/how-to/openlineage.md): where the output schema of each step ends up.
- [Examples](examples.md): the example jobs in this repository.
