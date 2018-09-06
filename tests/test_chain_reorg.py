"""test that chain reorgs are handled"""


def fetch_events(conn):
    with conn.cursor() as cur:
        cur.execute("select * from events order by blocknumber")
        rows = cur.fetchall()
        print(rows)
        return [event["args"]["_value"] for event in rows]


def test_reorg(testenv, event_emitter, conn, synchronizer):
    # event_emitter.add_some_tranfer_events adds 3 events increases the value
    # added by one for each event

    event_emitter.add_some_tranfer_events()  # add events with values 0, 1, 2
    snapshot = testenv.ethereum_tester.take_snapshot()
    event_emitter.add_some_tranfer_events()  # add events with values 3, 4, 5
    synchronizer.sync_until_current()
    values_before = fetch_events(conn)
    assert values_before == [0, 1, 2, 3, 4, 5]

    # now reorg the chain
    testenv.ethereum_tester.revert_to_snapshot(snapshot)
    event_emitter.add_some_tranfer_events()  # add events with values 6, 7, 8
    event_emitter.add_some_tranfer_events()  # add events with values 9, 10, 11
    synchronizer.sync_until_current()
    values_after = fetch_events(conn)
    assert values_after == [0, 1, 2, 6, 7, 8, 9, 10, 11]
