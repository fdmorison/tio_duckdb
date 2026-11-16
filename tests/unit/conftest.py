from collections.abc import Generator
from typing import Any

import duckdb
import pytest
from duckdb import DuckDBPyConnection
from tiozin import Context

from tests.stubs import InputStub, JobStub, RunnerStub
from tio_duckdb import DuckdbRunner


@pytest.fixture(scope="session", autouse=True)
def duckdb_conn() -> Generator[DuckDBPyConnection, Any, None]:
    conn = duckdb.connect(":memory:")
    yield conn
    conn.close()


@pytest.fixture(autouse=True)
def duckdb_runner_stub(duckdb_conn: DuckDBPyConnection) -> RunnerStub:
    runner_stub = RunnerStub(name="test_runner")
    runner_stub._session = duckdb_conn
    return runner_stub


@pytest.fixture(autouse=True)
def duckdb_job_stub(duckdb_runner_stub: RunnerStub) -> JobStub:
    return JobStub(
        name="test_job",
        org="acme",
        region="latam",
        domain="ecommerce",
        subdomain="checkout",
        layer="raw",
        product="sales",
        model="orders",
        runner=duckdb_runner_stub,
        inputs=[InputStub(name="test_input")],
    ).unwrap()


@pytest.fixture(autouse=True)
def duckdb_session(duckdb_job_stub: JobStub) -> Generator[Any, Any, None]:
    with Context.for_job(duckdb_job_stub) as context:
        yield context.runner.session


@pytest.fixture
def duckdb_runner() -> Generator[DuckdbRunner, Any, None]:
    """Returns a raw DuckdbRunner already set up with an in-memory connection."""
    runner: DuckdbRunner = DuckdbRunner(database=":memory:").__wrapped__
    runner.setup()
    yield runner
    runner.teardown()
