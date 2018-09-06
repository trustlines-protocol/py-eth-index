"""test that chain reorgs are handled"""

import pytest


def fetch_events(conn):
    with conn.cursor() as cur:
        cur.execute("select * from events order by blocknumber")
        rows = cur.fetchall()
        print(rows)
        return [event["args"]["_value"] for event in rows]


def test_reorg(testenv, event_emitter, conn, synchronizer):
    # event_emitter.add_some_tranfer_events adds 3 events and increases the value
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


@pytest.mark.xfail
def test_reorg_shorter_chain(testenv, event_emitter, conn, synchronizer):
    """test that reorgs that result in a shorter chain are handled

    The chain could get shorter since it only has to be the longest chain difficulty-wise.
    Not sure if this is only a theoretical problem.
    """
    # event_emitter.add_some_tranfer_events adds 3 events and increases the value
    # added by one for each event

    event_emitter.add_some_tranfer_events()  # add events with values 0, 1, 2
    snapshot = testenv.ethereum_tester.take_snapshot()
    event_emitter.add_some_tranfer_events()  # add events with values 3, 4, 5
    event_emitter.add_some_tranfer_events()  # add events with values 6, 7, 8
    synchronizer.sync_until_current()
    values_before = fetch_events(conn)
    print("values_before", values_before)
    assert values_before == [0, 1, 2, 3, 4, 5, 6, 7, 8]

    # now reorg the chain
    testenv.ethereum_tester.revert_to_snapshot(snapshot)
    event_emitter.add_some_tranfer_events()  # add events with values 9, 10, 11
    synchronizer.sync_until_current()
    values_after = fetch_events(conn)
    print("values_after", values_after)
    assert values_after == [0, 1, 2, 9, 10, 11]
