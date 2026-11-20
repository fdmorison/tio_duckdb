# tio_duckdb

`tio_duckdb` is the DuckDB family for [Tiozin](https://github.com/fdmorison/tiozin). It provides Tiozin plugins that run data jobs on a local [DuckDB](https://duckdb.org/docs/) connection.

A family is an installable package of Tiozin plugins that share the same runtime. See [The Family Model](https://github.com/fdmorison/tiozin/blob/main/docs/concepts/family.md) for how families fit into Tiozin.

## Usage

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

Neither `runner:` block sets more than the `kind`. Arguments that a job leaves out can come from `tiozin.yaml`, the [Tiozin settings file](https://github.com/fdmorison/tiozin/blob/main/docs/settings/index.md).

## Installation

`tio_duckdb` is installed as a Python dependency. Once it is installed, its plugins are available in any job.

The package has no extras, and it brings [DuckDB](https://duckdb.org/docs/) as a dependency.

```bash
pip install tio_duckdb
```

Add it to the project's dependencies, such as in `pyproject.toml`:

```toml
[project]
dependencies = [
  "tio_duckdb",
]
```

## Setting Up tiozin.yaml

`tiozin.yaml` is the [Tiozin settings file](https://github.com/fdmorison/tiozin/blob/main/docs/settings/index.md). It configures [registries](https://github.com/fdmorison/tiozin/blob/main/docs/settings/index.md#registries), such as the job and schema registries, and default plugin arguments under [`runtime_defaults`](https://github.com/fdmorison/tiozin/blob/main/docs/settings/index.md#runtime-defaults).

The example settings use `runtime_defaults` to connect DuckdbPostgresOutput to [PostgreSQL](https://www.postgresql.org/docs/).

1. Copy the `.env.example` file to `.env` at the repository root, then fill in the PostgreSQL variables in the `.env` file. The `.env` file is gitignored.

   ```bash
   cp .env.example .env
   ```

2. Copy the `tiozin.example.yaml` file to `tiozin.yaml` at the repository root. The `tiozin.yaml` file is gitignored.

   ```bash
   cp tiozin.example.yaml tiozin.yaml
   ```

3. Find the PostgreSQL connection settings under `runtime_defaults`. They give [DuckdbPostgresOutput](https://github.com/fdmorison/tio_duckdb/blob/main/docs/postgres-output.md) its schema, database, port, and credentials. The credentials are read from environment variables:

   ```yaml
   runtime_defaults:

     - kind: DuckdbPostgresOutput
       schema: public
       database: postgres
       port: 5432
       user: "{{ ENV.PGUSER | default('postgres') }}"
       password: "{{ ENV.PGPASSWORD | default('postgres') }}"
   ```

   A job that leaves these fields out takes them from here. The `user` and `password` values come from the `PGUSER` and `PGPASSWORD` variables in the `.env` file, and fall back to `postgres` when a variable is not set.

   If a job sets no `host`, DuckdbPostgresOutput reads it from the `PGHOST` variable.

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
