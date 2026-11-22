# tio_duckdb

`tio_duckdb` is the DuckDB [family](https://github.com/fdmorison/tiozin/blob/main/docs/concepts/family.md) for [Tiozin](https://github.com/fdmorison/tiozin): plugins that run data jobs on a local [DuckDB](https://duckdb.org/docs/) connection.

## One-Minute Example

```bash
pip install tio_duckdb
```

This job loads the text of Hamlet into a data lake. [DuckdbRunner](https://github.com/fdmorison/tio_duckdb/blob/main/docs/runner.md) runs it, [DuckdbFileInput](https://github.com/fdmorison/tio_duckdb/blob/main/docs/file-input.md) reads the text, and [DuckdbFileOutput](https://github.com/fdmorison/tio_duckdb/blob/main/docs/file-output.md) writes it.

```yaml
kind: LinearJob
name: ingestion_hamlet_job
owner: literature@tiozin.com
maintainer: tiozin
cost_center: tio_scrooge

org: tiozin
region: latam
domain: literature
subdomain: classics
product: shakespeare
model: hamlet
layer: raw

runner:
  kind: DuckdbRunner

inputs:
  - kind: DuckdbFileInput
    name: load_hamlet
    path: examples/data/{{product}}/{{model}}.txt
    format: text

outputs:
  - kind: DuckdbFileOutput
    name: save_hamlet
    path: .output/lake-{{domain}}-{{layer}}/{{product}}/{{model}}/date={{today}}
```

Run it:

```bash
tiozin run examples/jobs/oneminute.yaml
```

## Plugins

- [DuckdbRunner](https://github.com/fdmorison/tio_duckdb/blob/main/docs/runner.md): runs a job on a DuckDB connection that it opens during setup and closes during teardown.
- [DuckdbFileInput](https://github.com/fdmorison/tio_duckdb/blob/main/docs/file-input.md): reads files in any format DuckDB reads natively, such as Parquet, CSV, JSON, and plain text.
- [DuckdbSqlTransform](https://github.com/fdmorison/tio_duckdb/blob/main/docs/sql-transform.md): runs a SQL query over the results of earlier steps.
- [DuckdbWordCountTransform](https://github.com/fdmorison/tio_duckdb/blob/main/docs/examples.md#shakespeare): counts word occurrences in a text column.
- [DuckdbFileOutput](https://github.com/fdmorison/tio_duckdb/blob/main/docs/file-output.md): writes the result of a job to files in a directory.
- [DuckdbPostgresOutput](https://github.com/fdmorison/tio_duckdb/blob/main/docs/postgres-output.md): writes the result of a job into a [PostgreSQL](https://www.postgresql.org/docs/) table.

The package also exports the base classes `DuckdbInput`, `DuckdbTransform`, `DuckdbCoTransform`, and `DuckdbOutput` for writing custom steps. See [Accessing the connection](https://github.com/fdmorison/tio_duckdb/blob/main/docs/index.md#accessing-the-connection).

## Documentation

### Getting Started
- [Installation](https://github.com/fdmorison/tio_duckdb/blob/main/docs/installation.md)
- [Getting Started](https://github.com/fdmorison/tio_duckdb/blob/main/docs/getting-started.md)
- [Examples](https://github.com/fdmorison/tio_duckdb/blob/main/docs/examples.md)

### Using the Family
- [The DuckDB Family](https://github.com/fdmorison/tio_duckdb/blob/main/docs/index.md)
- [How Data Flows Through Steps](https://github.com/fdmorison/tio_duckdb/blob/main/docs/index.md#how-data-flows-through-steps)
- [Schemas Guide](https://github.com/fdmorison/tio_duckdb/blob/main/docs/schemas.md)
- [Accessing the Connection in Custom Steps](https://github.com/fdmorison/tio_duckdb/blob/main/docs/index.md#accessing-the-connection)

### Tiozin
- [Tiozin](https://github.com/fdmorison/tiozin)
- [Family Model: Tios and Tiozins](https://github.com/fdmorison/tiozin/blob/main/docs/concepts/family.md)
- [Settings Guide](https://github.com/fdmorison/tiozin/blob/main/docs/settings/index.md)
- [Creating Pluggable Tiozins](https://github.com/fdmorison/tiozin/blob/main/docs/extending/tiozins.md)

### DuckDB
- [DuckDB Documentation](https://duckdb.org/docs/)

## License

This project is licensed under the [Mozilla Public License 2.0](https://github.com/fdmorison/tio_duckdb/blob/main/LICENSE).
