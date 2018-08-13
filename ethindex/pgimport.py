"""import ethereum events into postgres
"""
import sys
import json
import time
from web3 import Web3
import psycopg2
import psycopg2.extras
import binascii
import logging
import click
from ethindex import logdecode, util
from typing import Iterable

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


def get_events(web3, topic_index, fromBlock, toBlock) -> Iterable[logdecode.Event]:
    return [
        topic_index.decode_log(x)
        for x in get_logs(web3, topic_index.addresses, fromBlock, toBlock)
    ]


def hexlify(d):
    return "0x" + binascii.hexlify(d).decode()


def bytesArgsToHex(args):
    for key in args:
        if type(args[key]) is bytes:
            args[key] = hexlify(args[key])
    return args


def insert_event(cur, event: logdecode.Event) -> None:
    event.args = bytesArgsToHex(event.args)
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
            hexlify(event.transactionhash),
            event.blocknumber,
            event.address,
            event.name,
            json.dumps(event.args),
            hexlify(event.blockhash),
            event.transactionindex,
            event.logindex,
            event.timestamp,
        ),
    )


def insert_events(conn, events: Iterable[logdecode.Event]) -> None:
    with conn.cursor() as cur:
        for event in events:
            insert_event(cur, event)


def event_blocknumbers(events):
    """given a list of events returns the block numbers containing events"""
    return {ev.blocknumber for ev in events}


def connect(dsn):
    return psycopg2.connect(dsn, cursor_factory=psycopg2.extras.RealDictCursor)


def enrich_events(events: Iterable[logdecode.Event], blocks) -> None:
    block_by_number = {b["number"]: b for b in blocks}
    for e in events:
        block = block_by_number[e.blocknumber]
        if block["hash"] != e.blockhash:
            raise RuntimeError("bad hash! chain reorg?")
        e.timestamp = block["timestamp"]


def insert_sync_entry(conn, syncid, addresses, start_block=-1):
    """make sure we have at least one entry in the sync table"""

    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO SYNC (syncid, last_block_number, last_block_hash, addresses)
               VALUES (%s, %s, %s, %s)""",
            (syncid, start_block, "", list(addresses)),
        )


def ensure_default_entry(conn, start_block=-1):
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
        insert_sync_entry(conn, "default", addresses, start_block=start_block)


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

    def _sync_blocks(self, fromBlock, toBlock):
        events = get_events(self.web3, self.topic_index, fromBlock, toBlock)
        blocknumbers = event_blocknumbers(events)
        logger.info(
            "got %s events in %s out of %s blocks (%s -> %s)",
            len(events),
            len(blocknumbers),
            toBlock - fromBlock + 1,
            fromBlock,
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

    def sync_some_blocks(self, waittime):
        while 1:
            latest_block = self.web3.eth.getBlock("latest")
            latest_block_number = latest_block["number"]
            self._load_data_from_sync()
            fromBlock = self.last_block_number + 1
            toBlock = min(
                latest_block_number, self.last_block_number + self.blocks_per_round
            )
            if fromBlock <= toBlock:
                self._sync_blocks(fromBlock, toBlock)
            else:
                logger.info("already synced up to latest block %s", toBlock)
                time.sleep(waittime)


@click.command()
@click.option("--jsonrpc", help="jsonrpc URL to use", default="http://127.0.0.1:8545")
@click.option(
    "--waittime",
    help="time to sleep in milliseconds waiting for a new block",
    default=1000,
)
@click.option(
    "--startblock", help="Block from where events should be synced", default=-1
)
def runsync(jsonrpc, waittime, startblock):
    logging.basicConfig(level=logging.INFO)
    logger.info("version %s starting", util.get_version())

    # we like to survive a postgresql restart, so we need to catch errors here,
    # since we must create a new connection in that case.
    while 1:
        try:
            web3 = Web3(Web3.HTTPProvider(jsonrpc, request_kwargs={"timeout": 60}))
            with connect("") as conn:
                ensure_default_entry(conn)
                s = Synchronizer(conn, web3, "default")
                s.sync_some_blocks(waittime * 0.001)
        except Exception as e:
            logger.error(
                "An error occured in runsync. Will restart runsync in 10 seconds",
                exc_info=sys.exc_info(),
            )
            time.sleep(10)


def do_importabi(conn, addresses, contracts):
    a2abi = logdecode.build_address_to_abi_dict(
        json.load(open(addresses)), json.load(open(contracts))
    )
    logger.info("importing %s abis", len(a2abi))
    with conn:
        with conn.cursor() as cur:
            for contract_address, abi in a2abi.items():
                cur.execute(
                    """INSERT INTO abis (contract_address, abi)
                       VALUES (%s, %s)
                       ON CONFLICT(contract_address) DO NOTHING""",
                    (contract_address, json.dumps(abi)),
                )


@click.command()
@click.option("--addresses", default="addresses.json")
@click.option("--contracts", default="contracts.json")
def importabi(addresses, contracts):
    logging.basicConfig(level=logging.INFO)
    logger.info("version %s starting", util.get_version())
    do_importabi(connect(""), addresses, contracts)


def do_createtables(conn):
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE events (
                     transactionHash TEXT NOT NULL,
                     blockNumber INTEGER NOT NULL,
                     address TEXT NOT NULL,
                     eventName TEXT NOT NULL,
                     args JSONB,
                     blockHash TEXT NOT NULL,
                     transactionIndex INTEGER NOT NULL,
                     logIndex INTEGER NOT NULL,
                     timestamp INTEGER NOT NULL,
                     PRIMARY KEY(transactionHash, address, blockHash, transactionIndex, logIndex)
                   );

                  CREATE TABLE sync (
                    syncid TEXT NOT NULL PRIMARY KEY,
                    last_block_number INTEGER NOT NULL,
                    last_block_hash TEXT NOT NULL,
                    addresses TEXT[] NOT NULL
                  );

                  CREATE TABLE abis (
                    contract_address TEXT NOT NULL PRIMARY KEY,
                    abi JSONB NOT NULL
                  );"""
            )


@click.command()
def createtables():
    logging.basicConfig(level=logging.INFO)
    logger.info("version %s starting", util.get_version())
    logger.info("creating tables")
    do_createtables(connect(""))


def do_droptables(conn, force):
    with conn:
        with conn.cursor() as cur:
            for table in ["events", "sync", "abis"]:
                stmt = "DROP TABLE IF EXISTS {}".format(table)
                logger.info("executing %r", stmt)
                if force:
                    cur.execute(stmt)


@click.command()
@click.option("--force", help="really delete the tables", is_flag=True)
def droptables(force):
    """drop database tables"""
    logging.basicConfig(level=logging.INFO)
    logger.info("version %s starting", util.get_version())
    if not force:
        logger.warn("dry-run, please specify --force to really delete the tables")

    do_droptables(connect(""), force)

    sys.exit(0 if force else 1)  # just in case we forget to add --force
