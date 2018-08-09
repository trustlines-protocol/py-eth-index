import os
import testing.postgresql
import pytest
import psycopg2
import psycopg2.extras


@pytest.fixture(scope="session")
def postgresql_factory():
    # Generate Postgresql class which shares the generated database
    factory = testing.postgresql.PostgresqlFactory(cache_initialized_db=True)
    yield factory
    factory.clear_cache()


@pytest.fixture
def postgresql(postgresql_factory):
    postgresql = postgresql_factory()
    dsn = postgresql.dsn()
    os.environ["PGDATABASE"] = dsn["database"]
    os.environ["PGHOST"] = dsn["host"]
    os.environ["PGPORT"] = str(dsn["port"])
    os.environ["PGUSER"] = dsn["user"]
    yield postgresql
    postgresql.stop()


@pytest.fixture
def postgresql_dsn(postgresql):
    return postgresql.dsn()


@pytest.fixture
def conn(postgresql_dsn):
    return psycopg2.connect(
        **postgresql_dsn, cursor_factory=psycopg2.extras.RealDictCursor
    )
