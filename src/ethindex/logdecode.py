"""ethereum log decoding

This module provides some helper functions to do ethereum log decoding

See https://codeburst.io/deep-dive-into-ethereum-logs-a8d2047c7371 for a nice
explanation.
"""

import itertools
from typing import Any, Dict, List, Optional

import attr
import eth_abi
import eth_utils
import hexbytes


def replace_with_checksum_address(values: List[Any], types: List[str]) -> List[Any]:
    """returns a new list of values with addresses replaced with their checksum
    address """
    return [
        eth_utils.to_checksum_address(value) if _type == "address" else value
        for (value, _type) in zip(values, types)
    ]


def build_address_to_abi_dict(
    addresses_json: Dict[str, Any], compiled_contracts: Dict
) -> Dict[str, Dict]:
    """build a contract-address to abi mapping from addresses.json and the contracts.json

    This function doesn't read the json files, but instead expects the decoded
    json from those files.
    """
    res = {}

    def add_abi(contract_address, contract_name):
        res[eth_utils.to_checksum_address(contract_address)] = compiled_contracts[
            contract_name
        ]["abi"]

    for network in addresses_json["networks"]:
        add_abi(network, "CurrencyNetwork")

    if "unwEth" in addresses_json:
        add_abi(addresses_json["unwEth"], "UnwEth")
    if "exchange" in addresses_json:
        add_abi(addresses_json["exchange"], "Exchange")
    return res


def decode_non_indexed_inputs(abi, log):
    """decode non-indexed inputs from a log entry

    This one decodes the values stored in the 'data' field."""
    inputs = [input_ for input_ in abi["inputs"] if not input_["indexed"]]
    types = [input_["type"] for input_ in inputs]
    names = [input_["name"] for input_ in inputs]
    data = hexbytes.HexBytes(log["data"])
    values = eth_abi.decode_abi(types, data)
    return zip(names, replace_with_checksum_address(values, types))


def decode_indexed_inputs(abi, log):
    """decode indexed inputs from a log entry

    This one decodes the values stored in in topics fields (without topic 0)"""
    inputs = [input_ for input_ in abi["inputs"] if input_["indexed"]]
    types = [input_["type"] for input_ in inputs]
    names = [input_["name"] for input_ in inputs]
    values = [
        eth_abi.decode_single(type_, value)
        for type_, value in zip(types, log["topics"][1:])
    ]
    return zip(names, replace_with_checksum_address(values, types))


def get_event_abis(abi):
    return [some_abi for some_abi in abi if some_abi["type"] == "event"]


@attr.s(auto_attribs=True)
class Event:
    name: str
    args: Dict
    log: Dict
    timestamp: Optional[int]

    @property
    def blocknumber(self):
        return self.log["blockNumber"]

    @property
    def blockhash(self):
        return self.log["blockHash"]

    @property
    def transactionhash(self):
        return self.log["transactionHash"]

    @property
    def address(self):
        return self.log["address"]

    @property
    def transactionindex(self):
        return self.log["transactionIndex"]

    @property
    def logindex(self):
        return self.log["logIndex"]


@attr.s(auto_attribs=True)
class GraphUpdate:
    name: str
    args: Dict
    address: str
    timestamp: Optional[int]


class TopicIndex:
    def __init__(self, address2abi):
        """build a TopicIndex from an contract address to ABI dict"""
        self.addresses = list(address2abi.keys())
        self.address2abi = address2abi
        self.address_topic2event_abi = {}
        for address, abi in self.address2abi.items():
            for event_abi in get_event_abis(abi):
                self.address_topic2event_abi[
                    (
                        address,
                        hexbytes.HexBytes(eth_utils.event_abi_to_log_topic(event_abi)),
                    )
                ] = event_abi

    def get_abi_for_log(self, log):
        return self.address_topic2event_abi.get((log["address"], log["topics"][0]))

    def decode_log(self, log) -> Event:
        abi = self.get_abi_for_log(log)
        if abi is None:
            raise RuntimeError("Could not find ABI for log %s", log)

        args = dict(
            itertools.chain(
                decode_non_indexed_inputs(abi, log), decode_indexed_inputs(abi, log)
            )
        )
        return Event(name=abi["name"], args=args, log=log, timestamp=None)
