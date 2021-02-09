import json
import os
from typing import Any, List

import attr
import eth_tester
import eth_utils
import psycopg2
import psycopg2.extras
import pytest
import testing.postgresql
from web3 import Web3
from web3.providers.eth_tester import EthereumTesterProvider

from ethindex import logdecode, pgimport


@pytest.fixture(scope="session")
def contracts_json_path():
    return os.path.normpath(os.path.join(__file__, "..", "build/contracts.json"))


@pytest.fixture(scope="session")
def compiled_contracts(contracts_json_path):
    with open(contracts_json_path) as contracts_json:
        return json.load(contracts_json)


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


def deploy_contract(web3, contract_interface):
    CurrencyNetwork = web3.eth.contract(
        abi=contract_interface["abi"], bytecode=contract_interface["bytecode"]
    )
    tx_hash = CurrencyNetwork.constructor().transact()
    tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
    return tx_receipt.contractAddress


@attr.s(auto_attribs=True)
class TestEnv:
    web3: Web3
    contract_addresses: List[str]
    currency_networks: List[Any]
    addresses_json_path: str
    contracts_json_path: str
    contracts: List[Any]
    abi: Any
    topic_index: logdecode.TopicIndex
    ethereum_tester: eth_tester.EthereumTester


@pytest.fixture
def testenv(
    ethereum_tester: eth_tester.EthereumTester,
    compiled_contracts,
    tmpdir,
    contracts_json_path,
):
    web3 = Web3(EthereumTesterProvider(ethereum_tester))
    web3.eth.defaultAccount = web3.eth.accounts[0]

    contract_interface = compiled_contracts["CurrencyNetworkOwnable"]
    contract_addresses = [deploy_contract(web3, contract_interface) for i in range(3)]
    currency_networks = [
        web3.eth.contract(address=contract_address, abi=contract_interface["abi"])
        for contract_address in contract_addresses
    ]

    addresses_json_path = tmpdir.join("addresses.json")
    addresses_json_path.write(json.dumps({"networks": contract_addresses}))
    snapshot = ethereum_tester.take_snapshot()
    abi = contract_interface["abi"]
    yield TestEnv(
        web3,
        contract_addresses,
        currency_networks,
        str(addresses_json_path),
        contracts_json_path,
        [
            web3.eth.contract(address=contract_address, abi=contract_interface["abi"])
            for contract_address in contract_addresses
        ],
        abi,
        logdecode.TopicIndex(
            {contract_address: abi for contract_address in contract_addresses}
        ),
        ethereum_tester,
    )
    ethereum_tester.revert_to_snapshot(snapshot)


@pytest.fixture
def web3_eth_tester(testenv):
    return testenv.web3


def make_address(i: int):
    return eth_utils.to_checksum_address("0x{:040X}".format(i))


class EventEmitter:
    """this class is used to emit events into the blockchain"""

    def __init__(self, testenv):
        self.testenv = testenv
        self.value = 0

    def add_some_tranfer_events(self):
        for i, contract in enumerate(self.testenv.contracts):
            contract.functions.makeTransfer(
                make_address(i), make_address(i + 1), self.value
            ).transact()
            self.value += 1

    def add_unknown_abi_events(self):
        for contract in self.testenv.contracts:
            contract.functions.emitUnknownAbiEvent().transact()


@pytest.fixture
def event_emitter(testenv):
    return EventEmitter(testenv)


@pytest.fixture
def synchronizer(testenv, conn):
    pgimport.do_createtables(conn)
    pgimport.do_importabi(
        conn, testenv.addresses_json_path, testenv.contracts_json_path
    )
    pgimport.ensure_default_entry(conn)
    synchronizer = pgimport.Synchronizer(
        conn, testenv.web3, "default", required_confirmations=10
    )
    return synchronizer
