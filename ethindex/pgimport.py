"""import ethereum events into postgres
"""
import json
import time
from web3 import Web3
import psycopg2
import psycopg2.extras
import binascii
import logging
import click
from ethindex import logdecode, util


logger = logging.getLogger(__name__)
# https://github.com/ethereum/wiki/wiki/JavaScript-API#web3ethgettransactionreceipt


def topic_index_from_db(conn, addresses=None):
    """create a logdecode.TopicIndex from the ABIs stored in the abis table"""
    with conn.cursor() as cur:
        if addresses is None:
            cur.execute("select * from abis")
        else:
            cur.execute(
                "select * from abis where contract_address in %s", (tuple(addresses),)
            )
        rows = cur.fetchall()
        return logdecode.TopicIndex({r["contract_address"]: r["abi"] for r in rows})


def get_logs(web3, addresses, fromBlock, toBlock):
    fromBlock = hex(fromBlock)
    if toBlock != "latest":
        toBlock = hex(toBlock)

    return web3.eth.getLogs(
        {"fromBlock": fromBlock, "toBlock": toBlock, "address": addresses}
    )


def get_events(web3, topic_index, fromBlock, toBlock):
    return [
        topic_index.decode_log(x)
        for x in get_logs(web3, topic_index.addresses, fromBlock, toBlock)
    ]


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

    with connect("") as conn:
        topic_index = topic_index_from_db(conn)

    events = get_events(web3, topic_index, 0, "latest")
    blocknumbers = event_blocknumbers(events)
    logger.info("got %s events in %s blocks", len(events), len(blocknumbers))
    blocks = [web3.eth.getBlock(x) for x in blocknumbers]
    enrich_events(events, blocks)

    with connect("") as conn:  # we rely on the PG* variables to be set
        insert_events(conn, events)


def insert_sync_entry(conn, syncid, addresses):
    """make sure we have at least one entry in the sync table"""

    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO SYNC (syncid, last_block_number, last_block_hash, addresses)
               VALUES (%s, %s, %s, %s)""",
            (syncid, 0, "", list(addresses)),
        )


def ensure_default_entry(conn):
    with conn.cursor() as cur:
        cur.execute("""select * from sync where syncid=%s""", ("default",))
        if cur.fetchall():
            return

        cur.execute("""select contract_address from abis""")
        addresses = [x["contract_address"] for x in cur.fetchall()]
        if not addresses:
            raise RuntimeError(
                "No ABIs found. Please add some ABIs first with 'ethindex importabi'"
            )
        insert_sync_entry(conn, "default", addresses)


class Synchronizer:
    blocks_per_round = 50000

    def __init__(self, conn, web3, syncid):
        self.conn = conn
        self.web3 = web3
        self.syncid = syncid

    def _load_data_from_sync(self):
        """load the current sync status for this job from the sync table

        This also locks the row in the sync table so no two sync jobs can run
        at the same time.
        """
        with self.conn.cursor() as cur:
            cur.execute(
                """SELECT * FROM sync WHERE syncid=%s FOR UPDATE""", (self.syncid,)
            )
            row = cur.fetchone()
            self.topic_index = topic_index_from_db(
                self.conn, addresses=row["addresses"]
            )
            self.last_block_number = row["last_block_number"]

    def sync_some_blocks(self):
        while 1:
            latest_block = self.web3.eth.getBlock("latest")
            latest_block_number = latest_block["number"]
            self._load_data_from_sync()
            toBlock = min(
                latest_block_number, self.last_block_number + self.blocks_per_round
            )
            events = get_events(
                self.web3, self.topic_index, self.last_block_number, toBlock
            )
            blocknumbers = event_blocknumbers(events)
            logger.info(
                "got %s events in %s blocks (%s -> %s)",
                len(events),
                len(blocknumbers),
                self.last_block_number,
                toBlock,
            )
            blocks = [self.web3.eth.getBlock(x) for x in blocknumbers]
            enrich_events(events, blocks)
            insert_events(self.conn, events)

            with self.conn.cursor() as cur:
                cur.execute(
                    """UPDATE sync SET last_block_number=%s where syncid=%s""",
                    (toBlock, self.syncid),
                )
            self.conn.commit()
            if toBlock == self.last_block_number:
                time.sleep(1)


@click.command()
@click.option("--jsonrpc", help="jsonrpc URL to use", default="http://127.0.0.1:8545")
def runsync(jsonrpc):
    logging.basicConfig(level=logging.INFO)
    logger.info("version %s starting", util.get_version())
    web3 = Web3(
        Web3.HTTPProvider(jsonrpc, request_kwargs={"timeout": 60})
    )

    with connect("") as conn:
        ensure_default_entry(conn)
        s = Synchronizer(conn, web3, "default")
        s.sync_some_blocks()


@click.command()
@click.option("--addresses", default="addresses.json")
@click.option("--contracts", default="contracts.json")
def importabi(addresses, contracts):
    logging.basicConfig(level=logging.INFO)
    logger.info("version %s starting", util.get_version())
    a2abi = logdecode.build_address_to_abi_dict(
        json.load(open(addresses)), json.load(open(contracts))
    )
    logger.info("importing %s abis", len(a2abi))
    with connect("") as conn:
        cur = conn.cursor()
        for contract_address, abi in a2abi.items():
            cur.execute(
                """INSERT INTO abis (contract_address, abi)
                   VALUES (%s, %s)
                   ON CONFLICT(contract_address) DO NOTHING""",
                (contract_address, json.dumps(abi)),
            )


if __name__ == "__main__":
    main()
