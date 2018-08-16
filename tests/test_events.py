import pytest
import eth_utils
from ethindex import pgimport


def make_address(i: int):
    return eth_utils.to_checksum_address("0x{:040X}".format(i))


@pytest.fixture
def add_some_tranfer_events(testenv):
    for i, contract in enumerate(testenv.contracts):
        contract.functions.makeTransfer(
            make_address(i), make_address(i + 1), i
        ).transact()


def test_get_events(testenv, add_some_tranfer_events):
    events = pgimport.get_events(testenv.web3, testenv.topic_index, 0, "latest")
    print("EVENTS:", len(events), events)

    assert [event.args for event in events] == [
        {
            "_value": 0,
            "_from": "0x0000000000000000000000000000000000000000",
            "_to": "0x0000000000000000000000000000000000000001",
        },
        {
            "_value": 1,
            "_from": "0x0000000000000000000000000000000000000001",
            "_to": "0x0000000000000000000000000000000000000002",
        },
        {
            "_value": 2,
            "_from": "0x0000000000000000000000000000000000000002",
            "_to": "0x0000000000000000000000000000000000000003",
        },
    ]


def test_topic_index_from_db(testenv, add_some_tranfer_events, conn):
    pgimport.do_createtables(conn)
    pgimport.do_importabi(
        conn, testenv.addresses_json_path, testenv.contracts_json_path
    )

    topic_index2 = pgimport.topic_index_from_db(conn)
    topic_index3 = pgimport.topic_index_from_db(conn, testenv.contract_addresses)

    assert set(topic_index2.addresses) == set(testenv.contract_addresses)
    assert set(topic_index3.addresses) == set(testenv.contract_addresses)

    events1 = pgimport.get_events(testenv.web3, testenv.topic_index, 0, "latest")
    events2 = pgimport.get_events(testenv.web3, topic_index2, 0, "latest")
    events3 = pgimport.get_events(testenv.web3, topic_index3, 0, "latest")
    assert events1 == events2
    assert events1 == events3
