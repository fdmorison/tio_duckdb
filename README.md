# tio_duckdb

`tio_duckdb` is the DuckDB family for [Tiozin](https://github.com/fdmorison/tiozin). It provides Tiozin plugins that run data jobs on a local [DuckDB](https://duckdb.org/docs/) connection.

A family is an installable package of Tiozin plugins that share the same runtime. See [The Family Model](https://github.com/fdmorison/tiozin/blob/main/docs/concepts/family.md) for how families fit into Tiozin.

## Installation

The package requires Python 3.11 or later and installs Tiozin 4.x and DuckDB as dependencies. It has no extras:

```bash
pip install tio_duckdb
```

## How Tiozin Finds It

Tiozin discovers the family automatically through the `tiozin.family` entry point. The family is registered as `tio_duckdb`, and its Python package is `tio_duckdb`.

After installation, its plugins are available by class name in any job:

```yaml
runner:
  kind: DuckdbRunner
```

If another installed family defines a class with the same name, qualify the kind with the family name:

```yaml
runner:
  kind: tio_duckdb:DuckdbRunner
```

## Plugins

- [DuckdbRunner](https://github.com/fdmorison/tio_duckdb/blob/main/docs/runner.md): runs a job on a DuckDB connection that it opens during setup and closes during teardown.
- [DuckdbFileInput](https://github.com/fdmorison/tio_duckdb/blob/main/docs/file-input.md): reads files in any format DuckDB reads natively, such as Parquet, CSV, JSON, and plain text.
- [DuckdbSqlTransform](https://github.com/fdmorison/tio_duckdb/blob/main/docs/sql-transform.md): runs a SQL query over the results of earlier steps.
- [DuckdbWordCountTransform](https://github.com/fdmorison/tio_duckdb/blob/main/docs/examples.md#shakespeare): counts word occurrences in a text column.
- [DuckdbFileOutput](https://github.com/fdmorison/tio_duckdb/blob/main/docs/file-output.md): writes the result of a job to files in a directory.
- [DuckdbPostgresOutput](https://github.com/fdmorison/tio_duckdb/blob/main/docs/postgres-output.md): writes the result of a job into a [PostgreSQL](https://www.postgresql.org/docs/) table.

The package also exports the base classes `DuckdbInput`, `DuckdbTransform`, `DuckdbCoTransform`, and `DuckdbOutput` for writing custom steps. See [Accessing the connection](https://github.com/fdmorison/tio_duckdb/blob/main/docs/index.md#accessing-the-connection).

The [family documentation](https://github.com/fdmorison/tio_duckdb/blob/main/docs/index.md) lists every plugin page.

## Learn More

- [Examples](https://github.com/fdmorison/tio_duckdb/blob/main/docs/examples.md)
- [Tiozin](https://github.com/fdmorison/tiozin)
- [DuckDB](https://duckdb.org/docs/)
