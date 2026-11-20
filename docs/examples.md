# Examples

The example jobs live in [`examples/jobs/`](../examples/jobs/), and their source data lives in [`examples/data/`](../examples/data/). The Ecommerce and Shakespeare scenarios are split into two layers: ingestion jobs load the source data, and refined jobs build new datasets from it.

Before running, complete the setup in [Getting Started](getting-started.md), then run every job from the repository root.

## Ecommerce

Ecommerce demonstrates tabular data: customers and orders from CSV files.

Ingestion jobs:

- [`ecommerce/ingestion_customers_job.yaml`](../examples/jobs/ecommerce/ingestion_customers_job.yaml): loads the customers.
- [`ecommerce/ingestion_orders_job.yaml`](../examples/jobs/ecommerce/ingestion_orders_job.yaml): loads the orders.

Refined jobs:

- [`ecommerce/refined_orders_job.yaml`](../examples/jobs/ecommerce/refined_orders_job.yaml): combines customers and orders into high-value orders.

Run the ingestion jobs first:

```bash
tiozin run examples/jobs/ecommerce/ingestion_customers_job.yaml
tiozin run examples/jobs/ecommerce/ingestion_orders_job.yaml
tiozin run examples/jobs/ecommerce/refined_orders_job.yaml
```

## Shakespeare

Shakespeare demonstrates textual data: four works of Shakespeare from text files.

Ingestion jobs:

- [`shakespeare/ingestion_job.yaml`](../examples/jobs/shakespeare/ingestion_job.yaml): loads all four works.

Refined jobs, one per work:

- [`shakespeare/refined_hamlet_job.yaml`](../examples/jobs/shakespeare/refined_hamlet_job.yaml): Hamlet.
- [`shakespeare/refined_kinglear_job.yaml`](../examples/jobs/shakespeare/refined_kinglear_job.yaml): King Lear.
- [`shakespeare/refined_loverscomplaint_job.yaml`](../examples/jobs/shakespeare/refined_loverscomplaint_job.yaml): A Lover's Complaint.
- [`shakespeare/refined_sonnets_job.yaml`](../examples/jobs/shakespeare/refined_sonnets_job.yaml): the Sonnets.

Run the ingestion job first:

```bash
tiozin run examples/jobs/shakespeare/ingestion_job.yaml
tiozin run examples/jobs/shakespeare/refined_hamlet_job.yaml
```

## PostgreSQL

PostgreSQL demonstrates loading data into a database: the customers from the `customers.csv` file go into a [PostgreSQL](https://www.postgresql.org/docs/) table.

- [`postgres/postgres_output.yaml`](../examples/jobs/postgres/postgres_output.yaml): loads the customers into the `public.customers` table.

The job connects to a PostgreSQL server on `localhost`, port `5432`, as the `postgres` user on the `postgres` database. Start the server before running the job, and set its password in the `PGPASSWORD` variable of the `.env` file.

```bash
tiozin run examples/jobs/postgres/postgres_output.yaml
```
