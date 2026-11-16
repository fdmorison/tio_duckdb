# Examples

All examples live under [`examples/jobs/`](../examples/jobs/) in the repository, and their source data lives under [`examples/data/`](../examples/data/). The schemas used by the ingestion jobs live under [`examples/schemas/`](../examples/schemas/). Each example is a self-contained job manifest that runs on a local [DuckDB](https://duckdb.org/docs/) connection through [DuckdbRunner](runner.md).

## How the Folder Structure Works

Jobs are grouped by data product, and each job within a product gets its own YAML file named after its layer or purpose:

```text
examples/jobs/
  ecommerce/
    ingestion_customers_job.yaml
    ingestion_orders_job.yaml
    refined_orders_job.yaml
  shakespeare/
    ingestion_job.yaml
    refined_hamlet_job.yaml
    refined_kinglear_job.yaml
    refined_loverscomplaint_job.yaml
    refined_sonnets_job.yaml
  postgres/
    postgres_output.yaml
```

One folder per data product. One YAML per job. No shared state between files.

Schemas live in their own folder, one file per schema subject, and each file is named after its subject. The files follow the [Open Data Contract Standard (ODCS)](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/schema/) schema object:

```text
examples/schemas/
  tiozin.eu.ecommerce.sales.raw.storefront.customers.yaml
  tiozin.eu.ecommerce.sales.raw.storefront.orders.yaml
  tiozin.latam.literature.classics.raw.shakespeare.shakespeare.yaml
```

## Before Running

Tiozin reads its settings from `tiozin.yaml` in the current directory. The repository ships those settings as [`tiozin.example.yaml`](../tiozin.example.yaml), and `tiozin.yaml` itself is gitignored. Without a `tiozin.yaml`, Tiozin falls back to its default settings, and the example jobs fail because their schemas are not found.

Copy the example settings into place at the repository root:

```bash
cp tiozin.example.yaml tiozin.yaml
```

The settings point the job registry at `examples/jobs` and the schema registry, a [FileSchemaRegistry](https://github.com/fdmorison/tiozin/blob/main/docs/tio_kernel/file-schema-registry.md), at `examples/schemas`. They read secrets from environment variables and use no-op lineage, batch, and metric registries.

Steps that declare `schema_subject: auto` look up a subject built from the job's `org`, `region`, `domain`, `subdomain`, `layer`, `product`, and `model` fields:

```yaml
subject_template: "{{org}}.{{region}}.{{domain}}.{{subdomain}}.{{layer}}.{{product}}.{{model}}"
# → tiozin.eu.ecommerce.sales.raw.storefront.customers
```

The ingestion jobs find their schemas in `examples/schemas` this way. See [How to Use Schemas in Jobs](https://github.com/fdmorison/tiozin/blob/main/docs/how-to/schemas.md) for how subjects are resolved.

The same file declares `runtime_defaults` for the DuckDB plugins. Tiozin fills any field a job leaves out from these defaults. For example, `DuckdbFileOutput` falls back to `format: parquet` and `mode: append`. See [Runtime Defaults](https://github.com/fdmorison/tiozin/blob/main/docs/settings/index.md#runtime-defaults) for how they apply.

The input paths in the jobs, such as `examples/data/ecommerce/customers.csv`, are relative to the repository root. Run the jobs from there:

```bash
tiozin run examples/jobs/ecommerce/ingestion_customers_job.yaml
```

The jobs write their results under `.output/` in the repository root.

If copying the file is not an option, pass the example settings directly with `--settings-path`:

```bash
tiozin --settings-path tiozin.example.yaml run examples/jobs/ecommerce/ingestion_customers_job.yaml
```

## Two Transform Styles

The examples show two approaches to business logic:

- **SQL transforms** ([DuckdbSqlTransform](sql-transform.md)): logic lives in the query, and the plugin is generic. The ecommerce examples follow this pattern.
- **Plugin transforms** (`DuckdbWordCountTransform`): logic is encapsulated in the plugin class, and the YAML only declares parameters. The Shakespeare refined jobs follow this pattern.

## Ecommerce

A two-step pipeline split across three jobs: raw ingestion for customers and orders, followed by a refined join. All three jobs read with [DuckdbFileInput](file-input.md) and write [Apache Parquet](https://parquet.apache.org/docs/) files with [DuckdbFileOutput](file-output.md).

The output paths are built from the job metadata fields `domain`, `layer`, `product`, and `model`:

```yaml
path: .output/lake-{{domain}}-{{layer}}/{{product}}/{{model}}
# → .output/lake-ecommerce-raw/storefront/customers
```

The refined job sets `layer: raw` and `model` on each input, so the same template points at the raw outputs of the ingestion jobs. See the [Templates Reference](https://github.com/fdmorison/tiozin/blob/main/docs/templates.md) for the available variables.

| File | What it shows |
|---|---|
| [`ecommerce/ingestion_customers_job.yaml`](../examples/jobs/ecommerce/ingestion_customers_job.yaml) | CSV ingestion of `examples/data/ecommerce/customers.csv` with `format: csv` and `header: true`, ingestion metadata columns (`_raw_run_id`, `_raw_nominal_date`, `_raw_created_at`, `_source_created_at`) added with `DuckdbSqlTransform` and `@data`, and output to `.output/lake-ecommerce-raw/storefront/customers` with `mode: overwrite` |
| [`ecommerce/ingestion_orders_job.yaml`](../examples/jobs/ecommerce/ingestion_orders_job.yaml) | Same ingestion pattern for `examples/data/ecommerce/orders.csv`, written to `.output/lake-ecommerce-raw/storefront/orders` with `mode: overwrite` |
| [`ecommerce/refined_orders_job.yaml`](../examples/jobs/ecommerce/refined_orders_job.yaml) | Both raw outputs read as inputs named `load_customers` and `load_orders`, joined in SQL by those names, chained transforms with `@data`, a parameterized query with `$min_total` and `args:`, and output to `.output/lake-ecommerce-refined/storefront/high_value_orders` with `mode: overwrite`, partitioned by `country` |

The refined job queries its inputs by step name because every step result is registered as a named view. See [How data flows through steps](index.md#how-data-flows-through-steps).

Run both ingestion jobs before `refined_orders_job.yaml`, which reads the files they write:

```bash
tiozin run examples/jobs/ecommerce/ingestion_customers_job.yaml
tiozin run examples/jobs/ecommerce/ingestion_orders_job.yaml
tiozin run examples/jobs/ecommerce/refined_orders_job.yaml
```

## Shakespeare

A multi-job pipeline using works of Shakespeare as the source dataset. An ingestion job loads the raw texts into the lake, partitioned by work. Each refined job then counts the words of one work independently, so a collection of independent jobs composes into a larger pipeline.

The ingestion job reads every `.txt` file with `format: text`, which puts each line in a `value` column. With `explode_filepath: true`, each row also gets file path columns such as `filestem`, the file name without extension. The output is partitioned by `filestem`, so each work lands in its own folder:

```yaml
path: .output/lake-{{domain}}-{{layer}}/{{product}}/{{model}}/date={{today}}
# → .output/lake-literature-raw/shakespeare/shakespeare/date=2026-01-17/filestem=hamlet
```

Each refined job reads one of those folders through `filestem={{model}}` in its input path. Both paths include `date={{today}}`, so the refined jobs read the partition the ingestion job wrote for the same date.

`DuckdbWordCountTransform` splits the `value` column into words, lowercases them, and counts each word. Its result has a `word` column and a `count` column.

| File | What it shows |
|---|---|
| [`shakespeare/ingestion_job.yaml`](../examples/jobs/shakespeare/ingestion_job.yaml) | Text ingestion from `examples/data/shakespeare/*.txt` with `format: text` and `explode_filepath: true`, written to `.output/lake-literature-raw/shakespeare/shakespeare/date={{today}}` with `mode: overwrite`, partitioned by `filestem` |
| [`shakespeare/refined_hamlet_job.yaml`](../examples/jobs/shakespeare/refined_hamlet_job.yaml) | Hamlet partition read with `DuckdbFileInput`, word count with `DuckdbWordCountTransform`, and output to `.output/lake-literature-refined/shakespeare/hamlet/date={{today}}` with `mode: overwrite` |
| [`shakespeare/refined_sonnets_job.yaml`](../examples/jobs/shakespeare/refined_sonnets_job.yaml) | Word count of the Sonnets |
| [`shakespeare/refined_kinglear_job.yaml`](../examples/jobs/shakespeare/refined_kinglear_job.yaml) | Word count of King Lear |
| [`shakespeare/refined_loverscomplaint_job.yaml`](../examples/jobs/shakespeare/refined_loverscomplaint_job.yaml) | Word count of A Lover's Complaint |

The Sonnets, King Lear, and A Lover's Complaint jobs do not set `mode` on their output, so they take `mode: append` from the runtime defaults.

Run the ingestion job before any refined job:

```bash
tiozin run examples/jobs/shakespeare/ingestion_job.yaml
tiozin run examples/jobs/shakespeare/refined_hamlet_job.yaml
```

## PostgreSQL

**[`postgres/postgres_output.yaml`](../examples/jobs/postgres/postgres_output.yaml)**

Loads `examples/data/ecommerce/customers.csv` into the [PostgreSQL](https://www.postgresql.org/docs/) table `public.customers` with [DuckdbPostgresOutput](postgres-output.md). The job uses `mode: merge` with `primary_key: id`, so existing customers are updated and new ones are inserted. After the write, `post_pgsql` grants privileges on the table and creates indexes on `email` and `country`.

The job connects to `localhost` on port `5432` as user `postgres`, using database `postgres`. A PostgreSQL server must be reachable there before the job runs.

The password comes from the `PGPASSWORD` environment variable and falls back to `postgres` when the variable is not set:

```yaml
password: "{{ ENV.PGPASSWORD | default('postgres') }}"
```

If the server uses a different password, export it before running the job:

```bash
export PGPASSWORD="my-password"
tiozin run examples/jobs/postgres/postgres_output.yaml
```
