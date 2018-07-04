"""ethereum log decoding

This module provides some helper functions to do ethereum log decoding

See https://codeburst.io/deep-dive-into-ethereum-logs-a8d2047c7371 for a nice
explanation.
"""

import hexbytes
import eth_abi
import itertools
import eth_utils


def build_address_to_abi_dict(addresses_json, compiled_contracts):
    """build a contract-address to abi mapping from addresses.json and the contracts.json

    This function doesn't read the json files, but instead expects the decoded
    json from those files.
    """
    res = {}

    def add_abi(a, n):
        res[eth_utils.to_checksum_address(a)] = compiled_contracts[n]["abi"]

    for network in addresses_json["networks"]:
        add_abi(network, "CurrencyNetwork")

    add_abi(addresses_json["unwEth"], "UnwEth")
    add_abi(addresses_json["exchange"], "Exchange")
    return res


def decode_non_indexed_inputs(abi, log):
    """decode non-indexed inputs from a log entry

    This one decodes the values stored in the 'data' field."""
    inputs = [x for x in abi["inputs"] if not x["indexed"]]
    types = [x["type"] for x in inputs]
    names = [x["name"] for x in inputs]
    data = hexbytes.HexBytes(log["data"])
    values = eth_abi.decode_abi(types, data)
    return zip(names, values)


def decode_indexed_inputs(abi, log):
    """decode indexed inputs from a log entry

    This one decodes the values stored in in topics fields (without topic 0)"""
    inputs = [x for x in abi["inputs"] if x["indexed"]]
    types = [x["type"] for x in inputs]
    names = [x["name"] for x in inputs]
    values = [eth_abi.decode_single(t, v) for t, v in zip(types, log["topics"][1:])]

    return zip(names, values)


def filter_events(abi):
    return [x for x in abi if x["type"] == "event"]


class TopicIndex:
    def __init__(self, address2abi):
        """build a TopicIndex from an contract address to ABI dict"""
        self.addresses = list(address2abi.keys())
        self.address2abi = address2abi
        self.address_topic2event_abi = {}
        for a, abi in self.address2abi.items():
            for evabi in filter_events(abi):
                self.address_topic2event_abi[
                    (a, hexbytes.HexBytes(eth_utils.event_abi_to_log_topic(evabi)))
                ] = evabi

    def get_abi_for_log(self, log):
        return self.address_topic2event_abi.get((log["address"], log["topics"][0]))

    def decode_log(self, log):
        abi = self.get_abi_for_log(log)
        if abi is None:
            return None

        args = dict(
            itertools.chain(
                decode_non_indexed_inputs(abi, log), decode_indexed_inputs(abi, log)
            )
        )

        return {"name": abi["name"], "args": args, "log": log}
