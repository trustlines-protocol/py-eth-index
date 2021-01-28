from ethindex import pgimport


def test_get_events(testenv, event_emitter):
    event_emitter.add_some_tranfer_events()
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


def test_topic_index_from_db(testenv, event_emitter, conn):
    event_emitter.add_some_tranfer_events()
    pgimport.do_createtables(conn)
    pgimport.do_importabi(
        conn, testenv.addresses_json_path, testenv.contracts_json_path
    )

    topic_index2 = pgimport.topic_index_from_db(conn)
    topic_index3 = pgimport.topic_index_from_db(conn, testenv.contract_addresses)

    assert set(topic_index2.addresses) == set(testenv.contract_addresses)
    assert set(topic_index3.addresses) == set(testenv.contract_addresses)

    events1 = pgimport.get_events(testenv.web3, testenv.topic_index, 0, "latest")
    assert events1
    events2 = pgimport.get_events(testenv.web3, topic_index2, 0, "latest")
    events3 = pgimport.get_events(testenv.web3, topic_index3, 0, "latest")
    assert events1 == events2
    assert events1 == events3


def test_should_not_crash_on_unknown_event(testenv, event_emitter, conn):
    """Test that the indexer will not emit an error when an unknown event is emitted from an indexed address"""
    for abi_element in testenv.abi:
        if abi_element["type"] == "event":
            assert (
                abi_element["name"] != "UnknownAbiEvent"
            ), "Remove the UnknownAbiEvent from the abi to run this test properly."

    event_emitter.add_unknown_abi_events()
    pgimport.do_createtables(conn)
    pgimport.do_importabi(
        conn, testenv.addresses_json_path, testenv.contracts_json_path
    )

    pgimport.get_events(testenv.web3, testenv.topic_index, 0, "latest")
