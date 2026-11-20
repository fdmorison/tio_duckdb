# tio_duckdb

`tio_duckdb` is the Tiozin provider family for [DuckDB](https://duckdb.org/docs/). It runs pipelines on a local DuckDB connection. Every step result is automatically available as a named relation for downstream SQL queries. The family is designed for single-node, in-memory or file-based workloads.

A family is an installable package of Tiozin plugins that share the same runtime. See [The Family Model](https://github.com/fdmorison/tiozin/blob/main/docs/concepts/family.md) for how families fit into Tiozin.

To add the family to a project, see [Installation](installation.md). To set up the settings the example jobs use, see [Getting Started](getting-started.md).

## Using the Plugins

Once the package is installed, its plugins are available by class name in any job:

```yaml
runner:
  kind: DuckdbRunner
```

If another installed family defines a class with the same name, qualify the kind with the family name:

```yaml
runner:
  kind: tio_duckdb:DuckdbRunner
```

DuckDB config options, such as `threads` and `memory_limit`, go directly in the runner. See [DuckDB config options](runner.md#duckdb-config-options).

## How Data Flows Through Steps

Every step in `tio_duckdb` produces a `DuckDBPyRelation`. After each step runs, the framework automatically registers that relation as a named temporary view using the step's `name` as the view name.

```yaml
inputs:
  - kind: DuckdbFileInput
    name: raw customers
    # → registered as the view raw_customers
    path: data/customers.csv

transforms:
  - kind: DuckdbSqlTransform
    name: filtered
    query: SELECT * FROM raw_customers WHERE status = 'active'
    # raw_customers is available because the input was registered under that name
```

This view registration happens at the framework level for all inputs and transforms. Steps inherit the registered views automatically.

## Components

- [DuckdbRunner](runner.md)
- [DuckdbFileInput](file-input.md)
- [DuckdbSqlTransform](sql-transform.md)
- [DuckdbFileOutput](file-output.md)
- [DuckdbPostgresOutput](postgres-output.md)
- [DuckdbWordCountTransform](examples.md#shakespeare)

To implement a custom Input, Transform, or Output from scratch, see [Creating Pluggable Tiozins](https://github.com/fdmorison/tiozin/blob/main/docs/extending/tiozins.md).

## Examples

[Examples](examples.md) lists the example jobs in this repository, which ingest and refine ecommerce and Shakespeare data on DuckDB and load customer data into PostgreSQL.

## Accessing the Connection

When writing a custom step in `tio_duckdb`, use `self.duckdb` to access the active DuckDB connection. `self` here refers to the step instance: any class that extends `DuckdbTransform`, `DuckdbCoTransform`, `DuckdbInput`, or `DuckdbOutput`.

```python
def transform(self, data: DuckDBPyRelation) -> DuckDBPyRelation:
    sql = f"SELECT * FROM {data.alias} WHERE amount > 100"
    return self.duckdb.sql(sql)
```

This connection is the one opened and managed by the runner. It is shared across all steps in the pipeline, so every step reads from and writes to the same DuckDB session. Do not open a new connection with `duckdb.connect()` inside a step: that would create an isolated session with no access to the data registered by other steps.

`self.duckdb` resolves to:

```python
conn = self.context.runner.session  # DuckDBPyConnection
```

Both are equivalent. `self.duckdb` is the idiomatic form.
