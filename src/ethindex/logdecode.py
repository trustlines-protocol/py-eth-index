"""ethereum log decoding

This module provides some helper functions to do ethereum log decoding

See https://codeburst.io/deep-dive-into-ethereum-logs-a8d2047c7371 for a nice
explanation.
"""

import itertools
import logging
from typing import Any, Dict, List, Optional

import attr
import eth_abi
import eth_utils
import hexbytes

logger = logging.getLogger(__name__)


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
        add_abi(network, "CurrencyNetworkOwnable")

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

    This one decodes the values stored in topics fields (without topic 0)"""
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


@attr.s(cmp=False)
class Event:
    name = attr.ib(type=str)
    args = attr.ib(type=Dict)
    log = attr.ib(type=Dict)
    timestamp = attr.ib(type=Optional[int])

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

    def __eq__(self, other):
        if type(other) != type(self):
            return False
        # When comparing events (e.g. figuring out new or missing events due to reorg)
        # We don't compare the exact log, but match other attributes.
        # This is useful for events reconstructed from the database where the full log is not stored.
        compared_attributes = set(
            attribute for attribute in dir(self) if not attribute.startswith("_")
        )
        compared_attributes.remove("log")
        for attribute in compared_attributes:
            if self.__getattribute__(attribute) != other.__getattribute__(attribute):
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)


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

    def decode_logs(self, logs) -> List[Event]:
        decoded_logs = []
        for log in logs:
            decoded_log = self.decode_log(log)
            if decoded_log is not None:
                decoded_logs.append(decoded_log)
        return decoded_logs

    def decode_log(self, log) -> Optional[Event]:
        abi = self.get_abi_for_log(log)
        if abi is None:
            logger.warning(f"Could not find abi for log {log}")
            return None

        args = dict(
            itertools.chain(
                decode_non_indexed_inputs(abi, log), decode_indexed_inputs(abi, log)
            )
        )
        return Event(name=abi["name"], args=args, log=log, timestamp=None)
