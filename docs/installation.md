# Installation

`tio_duckdb` is installed as a Python dependency. Once it is installed, its plugins are available in any job.

```bash
pip install tio_duckdb
```

The package has no extras, and it brings [DuckDB](https://duckdb.org/docs/) as a dependency.

## Requirements

- Python 3.11 or later.
- [Tiozin](https://github.com/fdmorison/tiozin) 6.0.0 or later.
- [DuckDB](https://duckdb.org/docs/) 1.4.4 or later, below 2.0.0.

Tiozin and DuckDB are dependencies of the package, so pip installs them along with `tio_duckdb`.

## Adding It to a Project

Add it to the project's dependencies, such as in the `pyproject.toml` file:

```toml
[project]
dependencies = [
  "tio_duckdb",
]
```

## Next Steps

- [Getting Started](getting-started.md): set up the settings the example jobs use.
- [tio_duckdb](index.md): how the family's plugins work together.
- [Examples](examples.md): the example jobs in this repository.
