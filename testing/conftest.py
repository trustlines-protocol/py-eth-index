import os
import testing.postgresql
import pytest
import psycopg2
import psycopg2.extras
import eth_tester
from web3 import Web3
from web3.providers.eth_tester import EthereumTesterProvider


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


@pytest.fixture(scope="session")
def ethereum_tester():
    """Returns an instance of an Ethereum tester"""
    tester = eth_tester.EthereumTester(eth_tester.PyEVMBackend())
    return tester


@pytest.fixture
def web3_eth_tester(ethereum_tester):
    web3 = Web3(EthereumTesterProvider(ethereum_tester))
    snapshot = ethereum_tester.take_snapshot()
    yield web3
    ethereum_tester.revert_to_snapshot(snapshot)
