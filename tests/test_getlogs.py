def test_getlogs(web3_eth_tester):
    """test that getLogs works with a list of addresses

    there is a regression in web3 4.5.0, which breaks our usage of getLogs see
    https://github.com/ethereum/web3.py/issues/999
    """
    web3_eth_tester.eth.getLogs(
        {
            "fromBlock": 1,
            "toBlock": 1,
            "address": [
                "0x55bdaAf9f941A5BB3EacC8D876eeFf90b90ddac9",
                "0xC0B33D88C704455075a0724AA167a286da778DDE",
            ],
        }
    )
