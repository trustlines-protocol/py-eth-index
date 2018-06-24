"""import ethereum events into postgres
"""
import json
from web3 import Web3
import psycopg2
import psycopg2.extras
import binascii
import logging
from ethindex import logdecode


logger = logging.getLogger(__name__)
# https://github.com/ethereum/wiki/wiki/JavaScript-API#web3ethgettransactionreceipt


def get_logs(web3, addresses):
    return web3.eth.getLogs(
        {"fromBlock": "0x0", "toBlock": "latest", "address": addresses}
    )


def get_events(web3):
    a2abi = logdecode.build_address_to_abi_dict(
        json.load(open("addresses.json")), json.load(open("contracts.json"))
    )
    topic_index = logdecode.TopicIndex(a2abi)
    return [topic_index.decode_log(x) for x in get_logs(web3, topic_index.addresses)]


def hexlify(d):
    return "0x" + binascii.hexlify(d).decode()


def insert_blocks(conn, blocks):
    with conn.cursor() as cur:
        for b in blocks:
            cur.execute(
                """INSERT INTO blocks (blockNumber, blockHash, timestamp)
                           VALUES (%s, %s, %s)""",
                (b["number"], hexlify(b["hash"]), b["timestamp"]),
            )


def insert_events(conn, events):
    with conn.cursor() as cur:
        for x in events:
            cur.execute(
                """INSERT INTO events (transactionHash,
                                       blockNumber,
                                       address,
                                       eventName,
                                       args,
                                       blockHash,
                                       transactionIndex,
                                       logIndex,
                                       timestamp)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    hexlify(x["log"]["transactionHash"]),
                    x["log"]["blockNumber"],
                    x["log"]["address"],
                    x["name"],
                    json.dumps(x["args"]),
                    hexlify(x["log"]["blockHash"]),
                    x["log"]["transactionIndex"],
                    x["log"]["logIndex"],
                    x["timestamp"],
                ),
            )


def event_blocknumbers(events):
    """given a list of events returns the block numbers containing events"""
    return {ev["log"]["blockNumber"] for ev in events}


def connect(dsn):
    return psycopg2.connect(dsn, cursor_factory=psycopg2.extras.RealDictCursor)


def enrich_events(events, blocks):
    block_by_number = {b["number"]: b for b in blocks}
    for e in events:
        blocknumber = e["log"]["blockNumber"]
        block = block_by_number[blocknumber]
        if block["hash"] != e["log"]["blockHash"]:
            raise RuntimeError("bad hash! chain reorg?")
        e["timestamp"] = block["timestamp"]


def main():
    logging.basicConfig(level=logging.INFO)
    web3 = Web3(
        Web3.HTTPProvider("http://127.0.0.1:8545", request_kwargs={"timeout": 60})
    )

    events = get_events(web3)
    blocknumbers = event_blocknumbers(events)
    logger.info("got %s events in %s blocks", len(events), len(blocknumbers))
    blocks = [web3.eth.getBlock(x) for x in blocknumbers]
    enrich_events(events, blocks)

    with connect("") as conn:  # we rely on the PG* variables to be set
        insert_events(conn, events)


if __name__ == "__main__":
    main()
