"""import ethereum events into postgres
"""
import json
from web3 import Web3
import psycopg2
import binascii

from ethidx import logdecode


# https://github.com/ethereum/wiki/wiki/JavaScript-API#web3ethgettransactionreceipt


def get_logs(addresses):

    web3 = Web3(
        Web3.HTTPProvider("http://127.0.0.1:8545", request_kwargs={"timeout": 60})
    )

    return web3.eth.getLogs(
        {"fromBlock": "0x0", "toBlock": "latest", "address": addresses}
    )


def get_events():
    a2abi = logdecode.build_address_to_abi_dict(
        json.load(open("addresses.json")), json.load(open("contracts.json"))
    )
    topic_index = logdecode.TopicIndex(a2abi)

    for x in get_logs(topic_index.addresses):
        yield topic_index.decode_log(x)


def hexlify(d):
    return "0x" + binascii.hexlify(d).decode()


def main():
    conn = psycopg2.connect("")  # we rely on the PG* variables to be set
    cur = conn.cursor()
    for x in get_events():
        cur.execute(
            """INSERT INTO events (transactionHash,
                                   blockNumber,
                                   address,
                                   eventName,
                                   args,
                                   blockHash,
                                   transactionIndex,
                                   logIndex)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                hexlify(x["log"]["transactionHash"]),
                x["log"]["blockNumber"],
                x["log"]["address"],
                x["name"],
                json.dumps(x["args"]),
                hexlify(x["log"]["blockHash"]),
                x["log"]["transactionIndex"],
                x["log"]["logIndex"],
            ),
        )
    conn.commit()


if __name__ == "__main__":
    main()
