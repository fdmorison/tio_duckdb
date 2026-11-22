# Schemas Guide

Tiozin captures the schema produced by each DuckDB step as the job runs. It reads the schema from the step's DuckDB relation, which represents a set of rows with named, typed columns. The schema records each column's name and type, reflecting the data at that point in the pipeline.

Tiozin includes this schema in the step's [lineage events](https://github.com/fdmorison/tiozin/blob/main/docs/how-to/openlineage.md#what-gets-emitted), using the [OpenLineage schema facet](https://openlineage.io/docs/spec/facets/dataset-facets/schema) to describe the dataset.

## See It in Action

The Hamlet example jobs demonstrate how schema extraction works. Complete the setup in [Getting Started](getting-started.md), then run both jobs from the repository root:

```bash
tiozin run examples/jobs/shakespeare/ingestion_job.yaml
tiozin run examples/jobs/shakespeare/refined_hamlet_job.yaml
```

The refined job counts the words in Hamlet:

```yaml
transforms:
  - kind: DuckdbWordCountTransform
    name: count_words
    content_field: value
    lowercase: true
```

After `count_words` runs, Tiozin captures this output schema:

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

The source of the schema depends on the step type:

- **Input and Transform:** Tiozin reads the schema from the relation returned by the step.
- **Output:** Tiozin reads the schema from the relation received by the step, before writing the data.

In both cases, Tiozin uses its canonical schema model. See [How to Use Schemas in Jobs](https://github.com/fdmorison/tiozin/blob/main/docs/how-to/schemas.md) for details.

## Add Documentation with a Contract

The schema extracted from a relation contains column names and types, but no descriptions. To document the data, Tiozin uses a schema contract retrieved from the registry through the step's `schema_subject`.

The contract supplies documentation for the schema Tiozin discovers at runtime. See [Attach a schema to a step](https://github.com/fdmorison/tiozin/blob/main/docs/how-to/schemas.md#attach-a-schema-to-a-step) to learn how Tiozin resolves the contract.

In the refined Hamlet job, the `load_poems` input uses a contract:

```yaml
inputs:
  - kind: DuckdbFileInput
    name: load_poems
    layer: raw
    path: .output/lake-{{domain}}-{{layer}}/{{product}}/{{product}}/date={{today}}/filestem={{model}}
    schema_subject: auto
    # → tiozin.latam.literature.classics.raw.shakespeare.hamlet
```

The contract is stored in [`examples/schemas/tiozin.latam.literature.classics.raw.shakespeare.hamlet.yaml`](../examples/schemas/tiozin.latam.literature.classics.raw.shakespeare.hamlet.yaml):

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

When a step has a contract, Tiozin copies its documentation, including descriptions, into the output schema. The contract documents the data; it does not define or modify the columns.

The following rules apply:

- Column names and types always come from the actual data.
- Columns missing from the contract remain in the output schema, but have no contract-provided description.
- Columns defined in the contract but absent from the data are not added.
- Constraints such as `required` are not copied into the output schema.

For `load_poems`, the result includes the documented `value` column and other columns discovered in the data:

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
  # ... one property for each remaining column
```

See [Evolve a Schema and Copy Its Documentation](https://github.com/fdmorison/tiozin/blob/main/docs/how-to/schemas.md#evolve-a-schema-and-copy-its-documentation) for the complete list of documentation fields Tiozin copies.

## Use the DuckDB Schema Format

The `duckdb` schema format represents a schema as a dictionary mapping each column name to its [DuckDB type](https://duckdb.org/docs/stable/sql/data_types/overview). This is the same format accepted by DuckDB's `read_csv(columns=...)`.

`tio_duckdb` registers a converter for this format, `DuckdbSchemaConverter`. The converter lets `Schema.from_format()` and `Schema.to_format()` convert between this dictionary and the canonical `Schema` model:

```python
import tio_duckdb
from tiozin import Schema

schema = Schema.from_format("duckdb", {"id": "BIGINT", "tags": "VARCHAR[]"})

schema.to_format("duckdb")
# → {"id": "BIGINT", "tags": "VARCHAR[]"}
```

Importing `tio_duckdb` registers the converter. Jobs using DuckDB plugins already import it.

The dictionary can also be passed as a JSON string:

```python
schema = Schema.from_format("duckdb", '{"id": "BIGINT", "tags": "VARCHAR[]"}')
```

Because this format stores only column names and types, it cannot preserve comments or nullability. Schemas loaded from a dictionary therefore have neither.

## Map DuckDB Types to the Canonical Schema

When Tiozin reads a DuckDB type, it maps it to the corresponding logical type in the canonical schema. Some types also carry additional details, shown below.

| DuckDB type | Logical type | Details |
|---|---|---|
| `BOOLEAN` | `boolean` | |
| `TINYINT`, `SMALLINT`, `INTEGER`, `BIGINT`, `HUGEINT` | `integer` | `format`: `i8`, `i16`, `i32`, `i64`, `i128` |
| `UTINYINT`, `USMALLINT`, `UINTEGER`, `UBIGINT`, `UHUGEINT` | `integer` | `format`: `u8`, `u16`, `u32`, `u64`, `u128` |
| `FLOAT`, `DOUBLE` | `number` | `format`: `f32`, `f64` |
| `DECIMAL(p,s)` | `number` | `precision` and `scale` |
| `VARCHAR` | `string` | |
| `UUID` | `string` | `format`: `uuid` |
| `BLOB` | `string` | `binary` |
| `DATE` | `date` | |
| `TIME` | `time` | `timeUnit`: `micros` |
| `TIMESTAMP_MS`, `TIMESTAMP`, `TIMESTAMP_NS` | `timestamp` | `timezone`: `false`; `timeUnit`: `millis`, `micros`, `nanos` |
| `TIMESTAMP WITH TIME ZONE` | `timestamp` | `timeUnit`: `micros` |
| `STRUCT(...)` | `object` | |
| `T[]` | `array` | |
| `T[n]` | `array` | `minItems` and `maxItems` set to `n` |
| `MAP(K, V)` | `map` | |

DuckDB aliases follow the same mappings as their underlying types. For example, `INT` maps like `INTEGER`, `TEXT` like `VARCHAR`, and `TIMESTAMPTZ` like `TIMESTAMP WITH TIME ZONE`.

When converting in the opposite direction, Tiozin builds each DuckDB type from the property's logical type, options, and Tiozin-specific conventions such as `precision` and `binary`. It does not use the property's `physicalType` to choose the output type.

If a property omits an optional detail, Tiozin applies these defaults:

- An `integer` without `format` becomes `BIGINT`.
- A `number` without `format` or `precision` becomes `DOUBLE`.
- A `number` with `precision` but no `scale` becomes `DECIMAL(p,0)`.
- A `timestamp` becomes `TIMESTAMP WITH TIME ZONE`.
- A `timestamp` with `timezone: false` uses `timeUnit` to select the type: `millis` becomes `TIMESTAMP_MS`, `micros` becomes `TIMESTAMP`, and `nanos` becomes `TIMESTAMP_NS`. Without `timeUnit`, it becomes `TIMESTAMP`.
- An `array` becomes a fixed-size `T[n]` when both `minItems` and `maxItems` equal `n`. Otherwise, it becomes `T[]`.

For example:

```python
schema = Schema().integer("id").number("total", precision=10, scale=2).timestamp("created_at")

schema.to_format("duckdb")
# → {"id": "BIGINT", "total": "DECIMAL(10,2)", "created_at": "TIMESTAMP WITH TIME ZONE"}
```

## Handle Unsupported Types

Not every type has a matching representation in both formats. When Tiozin cannot map a type, it raises `SchemaError`.

This happens when:

- A DuckDB type has no corresponding logical type, such as `INTERVAL` or `UNION`.
- A canonical property has no supported DuckDB type, such as a `vector`.
- An `integer` uses an unsupported `format`, such as `i128` or `u64`. Supported integer formats range from `i8` to `i64` and from `u8` to `u32`.

Steps use the same conversion process to build their output schemas. If the data contains an unsupported type, such as `INTERVAL`, schema extraction fails with `SchemaError`.

## Next Steps

- [How to Use Schemas in Jobs](https://github.com/fdmorison/tiozin/blob/main/docs/how-to/schemas.md): Learn about schema registries, subjects, and the canonical schema.
- [How to Configure OpenLineage](https://github.com/fdmorison/tiozin/blob/main/docs/how-to/openlineage.md): See how output schemas appear in lineage events.
- [Examples](examples.md): Explore the example jobs in this repository.