# Getting Started

The example jobs in this repository run with the example settings. Set them up once, at the repository root:

1. Copy the `.env.example` file to `.env`, then fill in the PostgreSQL variables in the `.env` file. The `.env` file is gitignored.

   ```bash
   cp .env.example .env
   ```

2. Copy the `tiozin.example.yaml` file to `tiozin.yaml`. The `tiozin.yaml` file is gitignored.

   ```bash
   cp tiozin.example.yaml tiozin.yaml
   ```

3. Run a job from the repository root:

   ```bash
   tiozin run examples/jobs/shakespeare/ingestion_job.yaml
   ```

## The tiozin.yaml File

The `tiozin.yaml` file is the [Tiozin settings file](https://github.com/fdmorison/tiozin/blob/main/docs/settings/index.md). It configures [registries](https://github.com/fdmorison/tiozin/blob/main/docs/settings/index.md#registries), such as the job and schema registries, and default plugin arguments under [`runtime_defaults`](https://github.com/fdmorison/tiozin/blob/main/docs/settings/index.md#runtime-defaults).

Tiozin looks for the `tiozin.yaml` file in the current directory first. See [How Tiozin Finds tiozin.yaml](https://github.com/fdmorison/tiozin/blob/main/docs/settings/index.md#how-tiozin-finds-tiozinyaml) for the other places it checks.

## Connecting to PostgreSQL

The example settings use `runtime_defaults` to connect [DuckdbPostgresOutput](postgres-output.md) to [PostgreSQL](https://www.postgresql.org/docs/). These connection settings give DuckdbPostgresOutput its schema, database, port, and credentials. The credentials are read from environment variables:

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

The PostgreSQL example job and the server it expects are described in [Examples](examples.md#postgresql).

## Next Steps

- [Examples](examples.md): every example job and the order to run them in.
- [Settings Guide](https://github.com/fdmorison/tiozin/blob/main/docs/settings/index.md): everything the `tiozin.yaml` file configures.
- [tio_duckdb](index.md): how the family's plugins work together.
